import type { BoardEvents, Cell } from "@/features/games.components/board.interaction.ts";
import type { usePuzzleState } from "@/composables/usePuzzleState.ts";

/**
 * Clear the solved state of the puzzle when a cell is clicked, as to not keep the puzzle marked with the
 * "Try Again" message on top.
 * @param session
 */
export function useClearStateBehaviour(session: Awaited<ReturnType<typeof usePuzzleState>>): Partial<BoardEvents> {
  return {
    onCellClick(_cell: Cell, _event: MouseEvent): boolean {
      session.session.clear_solved_state();
      return false;
    },
  };
}
