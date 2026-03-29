/**
 * use daily stores as backend for GameSessionServices interface.
 *
 * uses "daily" as the progress key, gets definition from useDailyPuzzleStore,
 * and submits to the daily endpoint on solve.
 */

import { computed, ref } from "vue";
import { useDailyPuzzleStore } from "@/core/store/puzzle/useDailyPuzzleStore";
import { usePuzzleProgressStore } from "@/core/store/puzzle/usePuzzleProgressStore";
import { usePuzzleHistoryStore } from "@/core/store/puzzle/usePuzzleHistoryStore";
import type { GameSessionServices } from "@/core/games/composables";
import type { PuzzleVariant } from "@/core/types";

const DAILY_KEY = "daily";

export function useDailyServices<TMeta = any>(): GameSessionServices<TMeta> {
  const daily_store = useDailyPuzzleStore();
  const progress_store = usePuzzleProgressStore();
  const history_store = usePuzzleHistoryStore();

  const definition = daily_store.definition;
  if (!definition) {
    throw new Error("daily puzzle definition not loaded");
  }

  const saved_board = ref<number[][] | null>(
    progress_store.current_puzzle_states[DAILY_KEY] ?? null
  );

  // don't auto-init progress — wait for explicit start_game() call
  // returning users already have timestamp_start so they skip this anyway
  async function start_game() {
    if (!progress_store.timestamp_start[DAILY_KEY]) {
      await progress_store.reset_puzzle(DAILY_KEY, definition.initial_state);
    }
  }

  const is_solved = computed(() => progress_store.is_puzzle_solved(DAILY_KEY));
  const formatted_time = computed(() => progress_store.get_formatted_time(DAILY_KEY));

  const current_variant = ref<PuzzleVariant>({
    size: daily_store.daily?.puzzle_size ?? "",
    difficulty: daily_store.daily?.puzzle_difficulty ?? null,
  });

  const tutorial_used = ref(progress_store.used_tutorial[DAILY_KEY] ?? false);

  async function mark_solved(): Promise<void> {
    await progress_store.mark_puzzle_solved(DAILY_KEY);

    const payload = history_store.get_upload_payload(DAILY_KEY, "freeplay");
    if (payload && daily_store.daily) {
      try {
        await fetch(`/api/puzzle/daily/${daily_store.daily.date}/submit`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify(payload),
        });
        await daily_store.refreshLeaderboard();
      } catch (err) {
        console.error("failed to submit daily attempt:", err);
      }
    }
  }

  function mark_tutorial_used(): void {
    if (!tutorial_used.value) {
      tutorial_used.value = true;
      progress_store.mark_tutorial_used(DAILY_KEY);
    }
  }

  async function request_new_puzzle() {
    // no-op for daily puzzles
    return null;
  }

  return {
    definition: ref(definition) as any,
    saved_board,
    is_solved,
    formatted_time,
    current_variant,
    tutorial_used,
    mark_solved,
    mark_tutorial_used,
    request_new_puzzle,
    start_game,
  };
}
