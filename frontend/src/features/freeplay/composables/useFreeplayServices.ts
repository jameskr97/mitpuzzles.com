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
import { useDailyPuzzleStore } from "@/core/store/puzzle/useDailyPuzzleStore.ts";
import { broadcast_channel_service } from "@/core/services/broadcast_channel.ts";
import { isDailyVariant } from "@/utils.ts";
import { capture_error } from "@/core/services/posthog.ts";
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

  /** Whether daily mode is active */
  is_daily: ComputedRef<boolean>;

  /** Current daily date (null when not in daily mode) */
  daily_date: Ref<string | null>;

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
  const daily_store = useDailyPuzzleStore();

  // register lifecycle hooks before any await
  const broadcast_unsubscribers: (() => void)[] = [];
  onUnmounted(() => {
    broadcast_unsubscribers.forEach((fn) => fn());
  });

  // Ensure stores are initialized
  await metadata_store.initializeStore();
  await progress_store.init();

  // Get initial variant selection and determine mode
  const selected = metadata_store.getSelectedVariant(puzzle_type);
  const is_daily = computed(() => isDailyVariant(metadata_store.getSelectedVariant(puzzle_type)));
  const daily_date = ref<string | null>(null);
  const current_variant = ref<[string, string]>(
    isDailyVariant(selected) ? ["", ""] : [selected[0], selected[1]]
  );

  // Dynamic progress key: changes between freeplay and daily modes
  const progress_key = computed(() =>
    is_daily.value && daily_date.value
      ? `daily:${daily_date.value}:${puzzle_type}`
      : puzzle_type
  );

  // Error state for when puzzle loading fails
  const error = ref<string | null>(null);

  // Load puzzle definition (branching on mode)
  let puzzle_definition: PuzzleDefinition<TMeta> | null = null;

  if (isDailyVariant(selected)) {
    try {
      await daily_store.ensureFresh();
      daily_date.value = daily_store.today_date;
      puzzle_definition = await daily_store.fetchDailyDefinition(daily_date.value, puzzle_type);
      if (puzzle_definition) {
        current_variant.value = [`${puzzle_definition.rows}x${puzzle_definition.cols}`, ""];
      }
    } catch (err) {
      capture_error("daily_puzzle_fetch_failed", err, { puzzle_type });
      error.value = "No daily puzzle available. Please check back later.";
    }
  } else {
    try {
      puzzle_definition = await definition_store.getOrFetchPuzzle<TMeta>(
        puzzle_type,
        current_variant.value[0],
        current_variant.value[1]
      );
    } catch (err) {
      capture_error("puzzle_fetch_failed", err, { puzzle_type });
      error.value = `No puzzles available for this game type. Please check back later.`;
    }
  }

  const definition = ref<PuzzleDefinition<TMeta> | null>(puzzle_definition);

  // Get saved board state using the current progress key
  const saved_board = ref<number[][] | null>(
    progress_store.current_puzzle_states[progress_key.value] ?? null
  );

  // Tutorial tracking
  const tutorial_used = ref(
    is_daily.value ? false : (progress_store.used_tutorial[puzzle_type] ?? false)
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
   * Request a new puzzle (or switch modes when variant changes)
   */
  async function request_new_puzzle(): Promise<PuzzleDefinition<TMeta> | null> {
    const variant = metadata_store.getSelectedVariant(puzzle_type);

    if (isDailyVariant(variant)) {
      // Daily mode: fetch today's puzzle
      try {
        await daily_store.ensureFresh();
        daily_date.value = daily_store.today_date;
        const new_def = await daily_store.fetchDailyDefinition(daily_date.value, puzzle_type);
        if (!new_def) {
          error.value = "No daily puzzle available. Please check back later.";
          return null;
        }
        error.value = null;
        definition.value = new_def;
        current_variant.value = [`${new_def.rows}x${new_def.cols}`, ""];

        // Load daily saved state
        const daily_key = `daily:${daily_date.value}:${puzzle_type}`;
        saved_board.value = progress_store.current_puzzle_states[daily_key] ?? null;
        tutorial_used.value = false;

        if (!progress_store.timestamp_start[daily_key] && saved_board.value === null) {
          await progress_store.reset_puzzle(daily_key, new_def.initial_state);
        }

        return new_def;
      } catch (err) {
        capture_error("daily_puzzle_fetch_failed", err, { puzzle_type });
        error.value = "No daily puzzle available. Please check back later.";
        return null;
      }
    } else {
      // Freeplay mode: fetch new random puzzle
      current_variant.value = [variant[0], variant[1]];
      daily_date.value = null;

      // Save incomplete attempt if any moves were made
      const events = history_store.get_events(puzzle_type, "freeplay");
      if (events.length > 0 && !is_solved.value) {
        try {
          await history_store.upload_attempt_history(puzzle_type, "freeplay");
        } catch (err) {
          capture_error("incomplete_attempt_save_failed", err, { puzzle_type });
        }
      }

      let new_definition: PuzzleDefinition<TMeta>;
      try {
        new_definition = await definition_store.requestNewPuzzle<TMeta>(
          puzzle_type,
          variant[0],
          variant[1]
        );
      } catch (err) {
        capture_error("puzzle_fetch_failed", err, { puzzle_type });
        error.value = `No puzzles available for this game type. Please check back later.`;
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
  }

  /**
   * Mark puzzle as solved
   */
  async function mark_solved(): Promise<void> {
    const pk = progress_key.value;
    await progress_store.mark_puzzle_solved(pk);

    if (is_daily.value && daily_date.value) {
      // Daily submission
      if (!definition.value) return;

      const events = history_store.get_events(pk, "freeplay");
      const action_history = events.map((event) => ({
        action: event.action_type,
        timestamp: event.timestamp,
        sequence: event.sequence,
        cell: event.cell,
        key: event.key,
        old_value: event.old_value,
        new_value: event.new_value,
        board_snapshot: event.board_snapshot,
        custom_data: event.custom_data,
      }));

      const payload = {
        puzzle_id: definition.value.id,
        timestamp_start: progress_store.timestamp_start[pk],
        timestamp_finish: progress_store.timestamp_finish[pk],
        action_history,
        board_state: progress_store.current_puzzle_states[pk] || [],
        is_solved: true,
        used_tutorial: tutorial_used.value,
      };

      try {
        await daily_store.submitDailyAttempt(daily_date.value, puzzle_type, payload);
        await daily_store.refreshDailyLeaderboard(daily_date.value, puzzle_type);
      } catch (err) {
        capture_error("daily_submit_failed", err, { puzzle_type, date: daily_date.value });
      }
    } else {
      // Freeplay submission
      await history_store.upload_attempt_history(pk, "freeplay");

      const [size, difficulty] = current_variant.value;
      const periods = ["today", "weekly", "monthly", "all_time"];
      const methods = ["best", "ao_n"];
      await Promise.all(
        periods.flatMap(period => methods.map(method =>
          leaderboard_store.refreshLeaderboard(puzzle_type, size, difficulty, period, method)
        ))
      );
    }
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
    definition,
    saved_board,
    current_variant,
    is_solved,
    tutorial_used,
    formatted_time,
    error,
    is_daily,
    daily_date,
    request_new_puzzle,
    mark_solved,
    reset_progress,
    mark_tutorial_used,
    save_board_state,
    upload_attempt_history,
  };
}
