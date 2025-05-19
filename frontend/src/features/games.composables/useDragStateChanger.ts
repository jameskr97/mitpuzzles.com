import { ref } from "vue";
import type { GameZone, Cell, BoardEvents } from "@/features/games.components/board.interaction.ts";
import { usePuzzleState } from "@/composables/usePuzzleState.ts";

/**
 * Composable handles mouse drag events to change the state of the puzzle board.
 */
export function useDragStateChanger(state: Awaited<ReturnType<typeof usePuzzleState>>): Partial<BoardEvents> {
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
    if (isMouseDown.value == false || cell.zone !== activeZone || firstClickedCell == null) return false;
    const desiredState = state.state.value?.board[firstClickedCell.row * state.state.value.cols + firstClickedCell.col];
    const currentState = state.state.value?.board[cell.row * state.state.value.cols + cell.col];

    // do nothing if the state is the same
    if (currentState === desiredState) return false;
    state.session.handle_cell_click(cell, event.button, desiredState);
    return true; // return true to indicate that the event was handled
  }

  return {
    onCellMouseDown,
    onMouseUp,
    onCellEnter,
  };
}
