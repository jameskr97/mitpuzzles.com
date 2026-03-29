/**
 * useGameForMode — dispatches to useFreeplayGame or useDailyGame
 * based on the "puzzle-type-override" injection from the parent view.
 */

import { inject } from "vue";
import { useFreeplayGame, type FreeplayGameConfig } from "@/features/freeplay/composables/useFreeplayGame";
import { useDailyGame } from "@/features/daily/composables/useDailyGame";
import type { GridGameReturn } from "@/core/games/types/game-return";
import type { GameSessionReturn } from "@/core/games/composables";

export async function useGameForMode<TReturn extends GridGameReturn<TMeta>, TMeta = any>(
  config: FreeplayGameConfig<TReturn, TMeta>
): Promise<GameSessionReturn<TReturn>> {
  const mode = inject<string | null>("puzzle-type-override", null);

  if (mode === "daily") {
    return useDailyGame({
      create_game: config.create_game,
      extra_puzzle_state: config.extra_puzzle_state,
    });
  }

  return useFreeplayGame(config);
}
