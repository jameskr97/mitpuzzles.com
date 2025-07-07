import type { BoardEvents, Cell } from "@/features/games.components/board.interaction.ts";
import type { PuzzleController } from "@/services/game/engines/types.ts";

export function useStateCycleBehaviour(ctrl: PuzzleController): Partial<BoardEvents> {
  return {
    /**
     * Tell the backend session that a cell was clicked.
     * The backend session decides what the meaning of a cell click is.
     * @param cell
     * @param event
     */
    onCellMouseDown(cell: Cell, event: MouseEvent): boolean {
      ctrl.handle_cell_click(cell, event);
      return false;
    },
  };
}
