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
    get_saveable_state: (game) => game.board.value,
    get_puzzle_state: (game, solved) => {
      const base: Record<string, any> = {
        definition: game.definition,
        board: game.board.value,
        solved,
      };
      if (game.immutable_cells) base.immutable_cells = game.immutable_cells.value;
      if (config.extra_puzzle_state) Object.assign(base, config.extra_puzzle_state(game));
      return base;
    },
    get_violations: (game) => game.get_violations(),
  });
}
