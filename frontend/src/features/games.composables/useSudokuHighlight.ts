import { computed, ref } from "vue";
import type { Cell } from "@/features/games.components/board.interaction.ts";
import type { usePuzzleState } from "@/composables/usePuzzleState.ts";

export function createSudokuBehavior(state: Awaited<ReturnType<typeof usePuzzleState>>) {
  const subgridSize = computed(() => Math.sqrt(state.state.value.rows ?? 0));
  const active_cell = ref<[number, number] | null>(null);

  function isRowSelected(row: number) {
    if (!active_cell.value) return false;
    return active_cell.value ? active_cell.value[0] === row : false;
  }

  function isColSelected(col: number) {
    if (!active_cell.value) return false;
    return active_cell.value ? active_cell.value[1] === col : false;
  }

  function isSquareSelected(row: number, col: number) {
    if (!active_cell.value) return false;
    const [active_row, active_col] = active_cell.value;

    return (
      Math.floor(active_row / subgridSize.value) === Math.floor(row / subgridSize.value) &&
      Math.floor(active_col / subgridSize.value) === Math.floor(col / subgridSize.value)
    );
  }

  function isCellActive(row: number, col: number) {
    if (!active_cell.value) return false;
    const [active_row, active_col] = active_cell.value;
    return active_row === row && active_col === col;
  }

  function clearActiveCell() {
    active_cell.value = null;
  }

  function onCellClick(cell: Cell, _event: MouseEvent): boolean {
    if (!state.state.value) return false;
    // @ts-expect-error state.state is not typed correctly yet
    const isFixed = state.state.value.board_initial[cell.row * state.state.value.cols + cell.col] !== 0;
    if (isFixed) return false; // Can't modify initial clues.
    active_cell.value = [cell.row, cell.col];
    return false;
  }

  function onCellKeyDown(cell: Cell, event: KeyboardEvent): boolean {
    // If the key is Escape, clear the active cell
    const key = event.key;
    if (key === "Escape") {
      clearActiveCell();
      return true;
    }

    if (!state.state.value) return false;
    const index = cell.row * state.state.value.cols + cell.col;

    // @ts-expect-error state.state is not typed correctly yet
    const isFixed = state.state.value.board_initial[index] !== 0;
    if (isFixed) return false; // Can't modify initial clues.
    const keyAsNumber = Number(key);
    // If key is not a number or is out of range, handle special keys
    if (isNaN(keyAsNumber) || keyAsNumber < 1 || keyAsNumber > state.state.value.rows) {
      // Handle special keys
      if (key === "Backspace" || key === "Delete") {
        state.state.value.board[index] = 0;
        state.session.handle_cell_click(cell, 0, 0);
        return true;
      }
      return false;
    }

    state.session.handle_cell_click(cell, 0, keyAsNumber);
    return true;
  }

  function shouldHighlightCell(row: number, col: number) {
    return isRowSelected(row) || isColSelected(col) || isSquareSelected(row, col);
  }

  return {
    isRowSelected,
    isColSelected,
    isSquareSelected,
    isCellActive,
    clearActiveCell,
    onCellClick,
    onCellKeyDown,
    shouldHighlightCell,
  };
}
