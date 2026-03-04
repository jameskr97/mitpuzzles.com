/**
 * useDailyServices - Services for daily challenge mode.
 *
 * Handles:
 * - Loading puzzle from daily API
 * - Timer tracking (uses daily-specific progress key)
 * - Submitting to daily endpoint
 */
import { computed, ref, type Ref, type ComputedRef } from "vue";
import { useDailyPuzzleStore } from "@/core/store/puzzle/useDailyPuzzleStore";
import { usePuzzleProgressStore } from "@/core/store/puzzle/usePuzzleProgressStore";
import { usePuzzleHistoryStore } from "@/core/store/puzzle/usePuzzleHistoryStore";
import { api } from "@/core/services/axios";
import type { PuzzleDefinition } from "@/core/games/types/puzzle-types";

export interface DailyServicesReturn<TMeta = any> {
  definition: Ref<PuzzleDefinition<TMeta> | null>;
  saved_board: Ref<number[][] | null>;
  current_variant: Ref<[string, string]>;
  is_solved: ComputedRef<boolean>;
  tutorial_used: Ref<boolean>;
  formatted_time: ComputedRef<string>;
  date: string;
  error: Ref<string | null>;
  mark_solved: () => Promise<void>;
  mark_tutorial_used: () => void;
}

export async function useDailyServices<TMeta = any>(
  puzzle_type: string
): Promise<DailyServicesReturn<TMeta>> {
  const daily_store = useDailyPuzzleStore();
  const progress_store = usePuzzleProgressStore();
  const history_store = usePuzzleHistoryStore();

  await progress_store.init();

  // Get today's date (re-fetches if date has rolled over)
  await daily_store.ensureFresh();
  const date = daily_store.today_date;

  const error = ref<string | null>(null);
  let puzzle_definition: PuzzleDefinition<TMeta> | null = null;

  try {
    puzzle_definition = await daily_store.fetchDailyDefinition(date, puzzle_type);
  } catch (err) {
    console.warn(`Failed to fetch daily puzzle for ${puzzle_type}:`, err);
    error.value = "No daily puzzle available. Please check back later.";
  }

  const definition = ref<PuzzleDefinition<TMeta> | null>(puzzle_definition);

  // Use a daily-specific progress key to avoid colliding with freeplay state
  const progress_key = `daily:${date}:${puzzle_type}`;
  const saved_board = ref<number[][] | null>(
    progress_store.current_puzzle_states[progress_key] ?? null
  );

  const tutorial_used = ref(false);

  // Derive variant from the definition (daily has no variant selector)
  const current_variant = ref<[string, string]>(
    definition.value
      ? [`${definition.value.rows}x${definition.value.cols}`, ""]
      : ["", ""]
  );

  // Initialize progress if first load
  if (!progress_store.timestamp_start[progress_key] && saved_board.value === null && definition.value) {
    await progress_store.reset_puzzle(progress_key, definition.value.initial_state);
  }

  const is_solved = computed(() => progress_store.is_puzzle_solved(progress_key));
  const formatted_time = computed(() => progress_store.get_formatted_time(progress_key));

  async function mark_solved(): Promise<void> {
    await progress_store.mark_puzzle_solved(progress_key);

    // Build payload and submit to daily endpoint
    if (!definition.value) return;

    const events = history_store.get_events(progress_key, "freeplay");
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
      timestamp_start: progress_store.timestamp_start[progress_key],
      timestamp_finish: progress_store.timestamp_finish[progress_key],
      action_history,
      board_state: progress_store.current_puzzle_states[progress_key] || [],
      is_solved: true,
      used_tutorial: tutorial_used.value,
    };

    try {
      await api.post(`/api/puzzle/daily/${date}/submit/${puzzle_type}`, payload);
      await daily_store.refreshDailyLeaderboard(date, puzzle_type);
    } catch (err) {
      console.error("Failed to submit daily attempt:", err);
    }
  }

  function mark_tutorial_used(): void {
    tutorial_used.value = true;
  }

  return {
    definition,
    saved_board,
    current_variant,
    is_solved,
    tutorial_used,
    formatted_time,
    date,
    error,
    mark_solved,
    mark_tutorial_used,
  };
}
