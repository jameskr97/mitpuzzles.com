import { ref } from "vue";
import type { GameZone, Cell, BoardEvents } from "@/features/games.components/board.interaction.ts";
import type { usePuzzleController } from "@/composables/usePuzzleController.ts";

/**
 * Composable handles mouse drag events to change the state of the puzzle board.
 */
export function useDragStateChanger(ctrl: ReturnType<typeof usePuzzleController>): Partial<BoardEvents> {
  const isMouseDown = ref(false);
  let activeZone: GameZone | null = null;
  let firstClickedCell: Cell | null = null;

  function onCellMouseDown(cell: Cell, _event: MouseEvent): boolean {
    isMouseDown.value = true;
    activeZone = cell.zone;
    firstClickedCell = cell;
    return false;
  }

  function onMouseUp(_: MouseEvent): boolean {
    isMouseDown.value = false;
    activeZone = null;
    return false;
  }

  function onCellEnter(cell: Cell, event: MouseEvent): boolean {
    if (isMouseDown.value == false || cell.zone !== "game" || firstClickedCell == null) return false;
    const desiredState = ctrl.state.value?.board[firstClickedCell.row * ctrl.state.value.cols + firstClickedCell.col];
    const currentState = ctrl.state.value?.board[cell.row * ctrl.state.value.cols + cell.col];

    // do nothing if the state is the same
    if (currentState === desiredState) return false;
    ctrl.handleCellClick(cell, event.button, desiredState);
    return true; // return true to indicate that the event was handled
  }

  return {
    onCellMouseDown,
    onMouseUp,
    onCellEnter,
  };
}
