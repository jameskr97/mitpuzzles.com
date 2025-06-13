import type { BoardEvents, Cell } from "@/features/games.components/board.interaction.ts";
import { inject } from "vue";
import { ModuleManager } from "@/services/eventbus.ts";
import type { GameModuleInterface } from "@/services/eventbus.modules/game.ts";
import { createPuzzleSession } from "@/composables/useCurrentPuzzle.ts";

/**
 * Clear the solved state of the puzzle when a cell is clicked, as to not keep the puzzle marked with the
 * "Try Again" message on top.
 * @param session
 */
export function useClearStateBehaviour(
  _session: Awaited<ReturnType<typeof createPuzzleSession>>,
): Partial<BoardEvents> {
  const event_modules = inject<ModuleManager>("event_modules");
  const game_module = event_modules?.getComposable?.<GameModuleInterface>("game");

  return {
    onCellClick(_cell: Cell, _event: MouseEvent): boolean {
      game_module?.clear_solved_state();
      return false;
    },
  };
}
