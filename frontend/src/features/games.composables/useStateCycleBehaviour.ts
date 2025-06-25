import type { BoardEvents, Cell } from "@/features/games.components/board.interaction.ts";
import type { usePuzzleController } from "@/composables/usePuzzleController.ts";

export function useStateCycleBehaviour(ctrl: ReturnType<typeof usePuzzleController>): Partial<BoardEvents> {

  return {
    /**
     * Tell the backend session that a cell was clicked.
     * The backend session decides what the meaning of a cell click is.
     * @param cell
     * @param event
     */
    onCellMouseDown(cell: Cell, event: MouseEvent): boolean {
      ctrl.handleCellClick(cell, event.button)
      return false;
    },
  };
}
