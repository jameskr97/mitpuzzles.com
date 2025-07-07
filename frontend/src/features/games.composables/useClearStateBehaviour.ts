import type { BoardEvents, Cell } from "@/features/games.components/board.interaction.ts";
import type { PuzzleController } from "@/services/game/engines/types.ts";

/**
 * Clear the solved state of the puzzle when a cell is clicked, as to not keep the puzzle marked with the
 * "Try Again" message on top.
 * @param ctrl
 */
export function useClearStateBehaviour(controller: PuzzleController): Partial<BoardEvents> {
  return {
    onCellClick(_cell: Cell, _event: MouseEvent): boolean {
      // controller.show_solved_state.value = false;
      return false;
    },
  };
}
