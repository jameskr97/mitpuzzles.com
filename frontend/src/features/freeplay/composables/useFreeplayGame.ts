import type { GridGameReturn } from "@/core/games/types/game-return.ts";
import type { PuzzleDefinition } from "@/core/games/types/puzzle-types.ts";
import { useFreeplayServices } from "@/features/freeplay/composables/useFreeplayServices.ts";
import { useGameSession, type GameSessionReturn } from "@/core/games/composables";

export type FreeplayGameReturn<TReturn extends GridGameReturn> = GameSessionReturn<TReturn>;

export interface FreeplayGameConfig<TReturn extends GridGameReturn<TMeta>, TMeta = any> {
  puzzle_type: string;
  create_game: (definition: PuzzleDefinition<TMeta>, saved_board: number[][] | null) => TReturn;
  extra_puzzle_state?: (game: TReturn) => Record<string, any>;
}

export async function useFreeplayGame<TReturn extends GridGameReturn<TMeta>, TMeta = any>(
  config: FreeplayGameConfig<TReturn, TMeta>
): Promise<FreeplayGameReturn<TReturn>> {
  const services = await useFreeplayServices<TMeta>(config.puzzle_type);

  return useGameSession({
    puzzle_type: config.puzzle_type,
    services,
    create_game: config.create_game,
    extra_puzzle_state: config.extra_puzzle_state,
  });
}
