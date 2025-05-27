import type { usePuzzleState } from "@/composables/usePuzzleState.ts";
import type { BoardEvents, Cell } from "@/features/games.components/board.interaction.ts";

export function useStateCycleBehaviour(session: Awaited<ReturnType<typeof usePuzzleState>>): Partial<BoardEvents> {
  return {
    /**
     * Tell the backend session that a cell was clicked.
     * The backend session decides what the meaning of a cell click is.
     * @param cell
     * @param event
     */
    onCellMouseDown(cell: Cell, event: MouseEvent): boolean {
      session.session.handle_cell_click(cell, event.button);
      return false;
    },
  };
}
