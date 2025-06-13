import type { BoardEvents, Cell } from "@/features/games.components/board.interaction.ts";
import { inject } from "vue";
import { ModuleManager } from "@/services/eventbus.ts";
import type { GameModuleInterface } from "@/services/eventbus.modules/game.ts";
import { createPuzzleSession } from "@/composables/useCurrentPuzzle.ts";

export function useStateCycleBehaviour(
  _session: Awaited<ReturnType<typeof createPuzzleSession>>,
): Partial<BoardEvents> {
  const event_modules = inject<ModuleManager>("event_modules");
  const game_module = event_modules?.getComposable?.<GameModuleInterface>("game");

  return {
    /**
     * Tell the backend session that a cell was clicked.
     * The backend session decides what the meaning of a cell click is.
     * @param cell
     * @param event
     */
    onCellMouseDown(cell: Cell, event: MouseEvent): boolean {
      game_module?.handle_cell_click(cell, event.button);
      return false;
    },
  };
}
