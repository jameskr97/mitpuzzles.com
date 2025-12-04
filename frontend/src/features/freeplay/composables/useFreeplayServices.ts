/**
 * useFreeplayServices - Combined services for freeplay mode
 *
 * Handles:
 * - Puzzle loading (initial + new puzzle requests)
 * - Board state persistence
 * - Variant (size/difficulty) management
 * - Timer tracking
 * - Tutorial mode
 * - Leaderboard integration
 */
import { computed, ref, type Ref, type ComputedRef, onUnmounted } from "vue";
import { usePuzzleDefinitionStore } from "@/core/store/puzzle/usePuzzleDefinitionStore.ts";
import { usePuzzleMetadataStore } from "@/core/store/puzzle/usePuzzleMetadataStore.ts";
import { usePuzzleProgressStore } from "@/core/store/puzzle/usePuzzleProgressStore.ts";
import { usePuzzleLeaderboardStore } from "@/core/store/puzzle/usePuzzleLeaderboardStore.ts";
import { usePuzzleHistoryStore } from "@/core/store/puzzle/usePuzzleHistoryStore.ts";
import { broadcast_channel_service } from "@/core/services/broadcast_channel.ts";
import type { PuzzleDefinition } from "@/core/games/types/puzzle-types.ts";

export interface FreeplayServicesReturn<TMeta = any> {
  /** Current puzzle definition (null if error loading) */
  definition: Ref<PuzzleDefinition<TMeta> | null>;

  /** Saved board state (null if starting fresh) */
  saved_board: Ref<number[][] | null>;

  /** Current variant [size, difficulty] */
  current_variant: Ref<[string, string]>;

  /** Whether puzzle is solved */
  is_solved: ComputedRef<boolean>;

  /** Whether tutorial was used */
  tutorial_used: Ref<boolean>;

  /** Formatted time string */
  formatted_time: ComputedRef<string>;

  /** Error message if puzzle loading failed */
  error: Ref<string | null>;

  /** Request a new puzzle */
  request_new_puzzle: () => Promise<PuzzleDefinition<TMeta> | null>;

  /** Mark puzzle as solved */
  mark_solved: () => Promise<void>;

  /** Reset puzzle progress (clear board) */
  reset_progress: (initial_board: number[][]) => Promise<void>;

  /** Mark tutorial as used */
  mark_tutorial_used: () => void;

  /** Save board state */
  save_board_state: (board: number[][]) => Promise<void>;

  /** Upload attempt history */
  upload_attempt_history: () => Promise<void>;
}

/**
 * Initialize freeplay services for a puzzle type
 */
export async function useFreeplayServices<TMeta = any>(
  puzzle_type: string
): Promise<FreeplayServicesReturn<TMeta>> {
  // Initialize stores
  const definition_store = usePuzzleDefinitionStore();
  const metadata_store = usePuzzleMetadataStore();
  const progress_store = usePuzzleProgressStore();
  const leaderboard_store = usePuzzleLeaderboardStore();
  const history_store = usePuzzleHistoryStore();

  // Ensure stores are initialized
  await metadata_store.initializeStore();
  await progress_store.init();

  // Get initial variant selection
  const selected = metadata_store.getSelectedVariant(puzzle_type);
  const current_variant = ref<[string, string]>([selected[0], selected[1]]);

  // Error state for when puzzle loading fails
  const error = ref<string | null>(null);

  // Load puzzle definition
  let puzzle_definition: PuzzleDefinition<TMeta> | null = null;
  try {
    puzzle_definition = await definition_store.getOrFetchPuzzle<TMeta>(
      puzzle_type,
      current_variant.value[0],
      current_variant.value[1]
    );
  } catch (err) {
    // Set error state when API fails (e.g., 404 - no puzzles available)
    console.warn(`Failed to fetch puzzle for ${puzzle_type}:`, err);
    error.value = `No puzzles available for this game type. Please check back later.`;
  }

  const definition = ref<PuzzleDefinition<TMeta> | null>(puzzle_definition);

  // Get saved board state
  const saved_board = ref<number[][] | null>(
    progress_store.current_puzzle_states[puzzle_type] ?? null
  );

  // Tutorial tracking
  const tutorial_used = ref(progress_store.used_tutorial[puzzle_type] ?? false);

  // Initialize progress if first load
  if (!progress_store.timestamp_start[puzzle_type] && saved_board.value === null) {
    // Will be initialized when game calls reset_progress
  }

  // Computed state
  const is_solved = computed(() => progress_store.is_puzzle_solved(puzzle_type));
  const formatted_time = computed(() => progress_store.get_formatted_time(puzzle_type));

  // Setup broadcast listeners for cross-tab sync
  const broadcast_unsubscribers: (() => void)[] = [];

  broadcast_unsubscribers.push(
    broadcast_channel_service.subscribe("game_state_update", (message) => {
      if (message.puzzle_type === puzzle_type) {
        saved_board.value = message.data.board_state;
      }
    })
  );

  broadcast_unsubscribers.push(
    broadcast_channel_service.subscribe("game_reset", (message) => {
      if (message.puzzle_type === puzzle_type) {
        saved_board.value = message.data.initial_state;
      }
    })
  );

  broadcast_unsubscribers.push(
    broadcast_channel_service.subscribe("new_puzzle", (message) => {
      if (message.puzzle_type === puzzle_type) {
        definition.value = message.data.puzzle_definition;
        saved_board.value = null;
        tutorial_used.value = false;
      }
    })
  );

  broadcast_unsubscribers.push(
    broadcast_channel_service.subscribe("tutorial_used", (message) => {
      if (message.puzzle_type === puzzle_type) {
        tutorial_used.value = true;
      }
    })
  );

  // Cleanup on unmount
  onUnmounted(() => {
    broadcast_unsubscribers.forEach((fn) => fn());
  });

  /**
   * Request a new puzzle
   */
  async function request_new_puzzle(): Promise<PuzzleDefinition<TMeta> | null> {
    // Save incomplete attempt if any moves were made
    const events = history_store.get_events(puzzle_type, "freeplay");
    if (events.length > 0 && !is_solved.value) {
      try {
        await history_store.upload_attempt_history(puzzle_type, "freeplay");
      } catch (err) {
        console.error("Failed to save incomplete attempt:", err);
      }
    }

    // Get current variant selection
    const variant = metadata_store.getSelectedVariant(puzzle_type);
    current_variant.value = [variant[0], variant[1]];

    // Request new puzzle
    let new_definition: PuzzleDefinition<TMeta>;
    try {
      new_definition = await definition_store.requestNewPuzzle<TMeta>(
        puzzle_type,
        variant[0],
        variant[1]
      );
    } catch (err) {
      // Set error state when API fails
      console.warn(`Failed to fetch new puzzle for ${puzzle_type}:`, err);
      error.value = `No puzzles available for this game type. Please check back later.`;
      return null;
    }

    // Clear any previous error
    error.value = null;
    definition.value = new_definition;
    saved_board.value = null;
    tutorial_used.value = false;

    // Clear history and reset timer
    await history_store.clear_events(puzzle_type, "freeplay");
    await progress_store.reset_puzzle(puzzle_type, new_definition.initial_state);

    // Broadcast to other tabs
    broadcast_channel_service.broadcast_new_puzzle(puzzle_type, new_definition);

    return new_definition;
  }

  /**
   * Mark puzzle as solved
   */
  async function mark_solved(): Promise<void> {
    await progress_store.mark_puzzle_solved(puzzle_type);

    // Upload history
    await history_store.upload_attempt_history(puzzle_type, "freeplay");

    // Refresh leaderboard
    const [size, difficulty] = current_variant.value;
    await leaderboard_store.refreshLeaderboard(puzzle_type, size, difficulty);
  }

  /**
   * Reset puzzle progress
   */
  async function reset_progress(initial_board: number[][]): Promise<void> {
    await progress_store.reset_puzzle(puzzle_type, initial_board);
    saved_board.value = initial_board;
  }

  /**
   * Mark tutorial as used
   */
  function mark_tutorial_used(): void {
    if (!tutorial_used.value) {
      tutorial_used.value = true;
      progress_store.mark_tutorial_used(puzzle_type);
    }
  }

  /**
   * Save board state
   */
  async function save_board_state(board: number[][]): Promise<void> {
    await progress_store.update_puzzle_state(puzzle_type, board);
    saved_board.value = board;
  }

  /**
   * Upload attempt history
   */
  async function upload_attempt_history(): Promise<void> {
    await history_store.upload_attempt_history(puzzle_type, "freeplay");
  }

  return {
    definition,
    saved_board,
    current_variant,
    is_solved,
    tutorial_used,
    formatted_time,
    error,
    request_new_puzzle,
    mark_solved,
    reset_progress,
    mark_tutorial_used,
    save_board_state,
    upload_attempt_history,
  };
}
