import { computed, ref, type Ref, type ComputedRef, onUnmounted } from "vue";
import { getCurrentPuzzleID, setCurrentPuzzleID } from "@/core/store/puzzle/usePuzzleDefinitionStore.ts";
import { usePuzzleMetadataStore } from "@/core/store/puzzle/usePuzzleMetadataStore.ts";
import { usePuzzleProgressStore } from "@/core/store/puzzle/usePuzzleProgressStore.ts";
import { usePuzzleHistoryStore } from "@/core/store/puzzle/usePuzzleHistoryStore.ts";
import { useSessionTrackingStore } from "@/core/store/useSessionTrackingStore.ts";
import { broadcast_channel_service } from "@/core/services/broadcast_channel.ts";
import { api } from "@/core/services/client";
import { capture_error } from "@/core/services/posthog.ts";
import type { PuzzleDefinition } from "@/core/games/types/puzzle-types.ts";
import type { PuzzleVariant } from "@/core/types";
import { emitter } from "@/core/services/event-bus.ts";

export interface FreeplayServicesReturn<TMeta = any> {
  /** Current puzzle definition (null if error loading) */
  definition: Ref<PuzzleDefinition<TMeta> | null>;

  /** Saved board state (null if starting fresh) */
  saved_board: Ref<number[][] | null>;

  /** current variant */
  current_variant: Ref<PuzzleVariant>;

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
  const session_store = useSessionTrackingStore();
  const metadata_store = usePuzzleMetadataStore();
  const progress_store = usePuzzleProgressStore();
  const history_store = usePuzzleHistoryStore();
  // register lifecycle hooks before any await
  const broadcast_unsubscribers: (() => void)[] = [];
  onUnmounted(() => {
    broadcast_unsubscribers.forEach((fn) => fn());
  });

  // fetch a new puzzle: request next ID, then fetch definition
  async function fetch_new_puzzle<T>(puzzle_type: string, variant: PuzzleVariant): Promise<PuzzleDefinition<T> | null> {
    const { data: idData, error: idError } = await api.GET("/api/puzzle/next", {
      params: { query: { puzzle_type, puzzle_size: variant.size, puzzle_difficulty: variant.difficulty, session_id: session_store.session_id } },
    });
    if (idError) {
      capture_error("next_puzzle_failed", idError, { puzzle_type, variant });
      return null;
    }

    setCurrentPuzzleID(puzzle_type, idData.puzzle_id);

    const { data: defData, error: defError } = await api.GET("/api/puzzle/definition/{puzzle_id}", {
      params: { path: { puzzle_id: idData.puzzle_id } },
    });
    if (defError) {
      capture_error("puzzle_definition_failed", defError, { puzzle_id: idData.puzzle_id });
      return null;
    }

    return defData as PuzzleDefinition<T>;
  }

  // ensure stores are initialized
  await metadata_store.initializeStore();
  await progress_store.init();

  const selected = metadata_store.getSelectedVariant(puzzle_type);
  const current_variant = ref<PuzzleVariant>(selected);
  const progress_key = computed(() => puzzle_type);
  const error = ref<string | null>(null);

  // load puzzle definition — try existing from localStorage, otherwise fetch new
  let puzzle_definition: PuzzleDefinition<TMeta> | null = null;
  const existing_id = getCurrentPuzzleID(puzzle_type);
  if (existing_id) {
    const { data } = await api.GET("/api/puzzle/definition/{puzzle_id}", {
      params: { path: { puzzle_id: existing_id } },
    });
    if (data) puzzle_definition = data as PuzzleDefinition<TMeta>;
  }
  if (!puzzle_definition) {
    puzzle_definition = await fetch_new_puzzle<TMeta>(puzzle_type, current_variant.value);
  }
  if (!puzzle_definition) {
    error.value = "No puzzles available for this game type. Please check back later.";
  }

  // sync selected variant to match the actual loaded puzzle
  if (puzzle_definition) {
    const actual_variant: PuzzleVariant = {
      size: puzzle_definition.puzzle_size,
      difficulty: puzzle_definition.puzzle_difficulty ?? null,
    };
    current_variant.value = actual_variant;
    metadata_store.set_selected_variant(puzzle_type, actual_variant);
  }

  const definition = ref<PuzzleDefinition<TMeta> | null>(puzzle_definition);

  // Get saved board state using the current progress key
  const saved_board = ref<number[][] | null>(
    progress_store.current_puzzle_states[progress_key.value] ?? null
  );

  // Tutorial tracking
  const tutorial_used = ref(
    progress_store.used_tutorial[puzzle_type] ?? false
  );

  // Initialize progress if first load
  if (!progress_store.timestamp_start[progress_key.value] && saved_board.value === null && definition.value) {
    await progress_store.reset_puzzle(progress_key.value, definition.value.initial_state);
  }

  // Computed state using dynamic progress key
  const is_solved = computed(() => progress_store.is_puzzle_solved(progress_key.value));
  const formatted_time = computed(() => progress_store.get_formatted_time(progress_key.value));

  // setup broadcast listeners for cross-tab sync

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

  /**
   * request a new puzzle
   */
  async function request_new_puzzle(): Promise<PuzzleDefinition<TMeta> | null> {
    const variant = metadata_store.getSelectedVariant(puzzle_type);
    current_variant.value = variant;

    // save incomplete attempt if any moves were made
    const events = history_store.get_events(puzzle_type, "freeplay");
    if (events.length > 0 && !is_solved.value) {
      try {
        await history_store.upload_attempt_history(puzzle_type, "freeplay");
      } catch (err) {
        capture_error("incomplete_attempt_save_failed", err, { puzzle_type });
      }
    }

    const new_definition = await fetch_new_puzzle<TMeta>(puzzle_type, variant);
    if (!new_definition) {
      capture_error("puzzle_fetch_failed", null, { puzzle_type, variant });
      error.value = "No puzzles available for this game type. Please check back later.";
      return null;
    }

    error.value = null;
    definition.value = new_definition;
    saved_board.value = null;
    tutorial_used.value = false;

    await history_store.clear_events(puzzle_type, "freeplay");
    await progress_store.reset_puzzle(puzzle_type, new_definition.initial_state);

    broadcast_channel_service.broadcast_new_puzzle(puzzle_type, new_definition);

    return new_definition;
  }

  /**
   * Mark puzzle as solved
   */
  async function mark_solved(): Promise<void> {
    const pk = progress_key.value;
    await progress_store.mark_puzzle_solved(pk);
    await history_store.upload_attempt_history(pk, "freeplay");
    emitter.emit("puzzle:solved:freeplay", { puzzle_type, variant: current_variant.value });
  }

  /**
   * Reset puzzle progress
   */
  async function reset_progress(initial_board: number[][]): Promise<void> {
    await progress_store.reset_puzzle(progress_key.value, initial_board);
    saved_board.value = initial_board;
  }

  /**
   * Mark tutorial as used
   */
  function mark_tutorial_used(): void {
    if (!tutorial_used.value) {
      tutorial_used.value = true;
      progress_store.mark_tutorial_used(progress_key.value);
    }
  }

  /**
   * Save board state
   */
  async function save_board_state(board: number[][]): Promise<void> {
    await progress_store.update_puzzle_state(progress_key.value, board);
    saved_board.value = board;
  }

  /**
   * Upload attempt history
   */
  async function upload_attempt_history(): Promise<void> {
    await history_store.upload_attempt_history(progress_key.value, "freeplay");
  }

  return {
    definition: definition as Ref<PuzzleDefinition<TMeta> | null>,
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
