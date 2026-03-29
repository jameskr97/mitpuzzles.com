/** thin wrapper over useGameSession for daily mode */
import type { GridGameReturn } from "@/core/games/types/game-return";
import type { PuzzleDefinition } from "@/core/games/types/puzzle-types";
import { useGameSession, type GameSessionReturn } from "@/core/games/composables";
import { useDailyServices } from "./useDailyServices";

export type DailyGameReturn<TReturn extends GridGameReturn> = GameSessionReturn<TReturn>;

export interface DailyGameConfig<TReturn extends GridGameReturn<TMeta>, TMeta = any> {
  create_game: (definition: PuzzleDefinition<TMeta>, saved_board: number[][] | null) => TReturn;
  extra_puzzle_state?: (game: TReturn) => Record<string, any>;
}

export function useDailyGame<TReturn extends GridGameReturn<TMeta>, TMeta = any>(
  config: DailyGameConfig<TReturn, TMeta>
): DailyGameReturn<TReturn> {
  const services = useDailyServices<TMeta>();

  return useGameSession({
    puzzle_type: "daily",
    services,
    create_game: config.create_game,
    extra_puzzle_state: config.extra_puzzle_state,
  });
}
