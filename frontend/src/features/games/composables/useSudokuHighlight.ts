import type { PuzzleStateSudoku } from "@/services/states.ts";
import type { Ref } from "vue";

export function useSudokuHighlight(stateRef: Ref<PuzzleStateSudoku>, squareSize: number) {
  const subgridSize = Math.sqrt(squareSize);

  function isRowSelected(row: number) {
    const active = stateRef.value.active_cell;
    return active ? active[0] === row : false;
  }

  function isColSelected(col: number) {
    const active = stateRef.value.active_cell;
    return active ? active[1] === col : false;
  }

  function isSquareSelected(row: number, col: number) {
    const active = stateRef.value.active_cell;
    if (!active) return false;
    const [active_row, active_col] = active;

    return (
      Math.floor(active_row / subgridSize) === Math.floor(row / subgridSize) &&
      Math.floor(active_col / subgridSize) === Math.floor(col / subgridSize)
    );
  }

  function shouldHighlightCell(row: number, col: number) {
    return isRowSelected(row) || isColSelected(col) || isSquareSelected(row, col);
  }

  return {
    isRowSelected,
    isColSelected,
    isSquareSelected,
    shouldHighlightCell,
  };
}
