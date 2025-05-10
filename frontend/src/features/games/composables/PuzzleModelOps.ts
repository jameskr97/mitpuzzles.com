import type { MutablePuzzleState } from "@/services/states.ts";

export class PuzzleModelOps {
  /**
   * changes the state of a board row or column in the following manner:
   * lets say we want to change all empty cells (fromState) to grass cells (toState).
   * 1. if a row/column contains a cell in fromState, change all in that row/column fromState to toState.
   * 2. if all cells in the row/column are in toState/fromState, toggle all cells between fromState/toState.
   * note: all cells that are not fromState or toState are ignored.
   *
   * @param isRow true if row, false if column
   * @param index index of the row/column
   * @param state the current puzzle state
   * @param fromState the state we want to toggle from
   * @param toState the state we want to toggle to
   */
  static changeLineState(
    isRow: boolean,
    index: number,
    state: MutablePuzzleState, // the current puzzle state
    fromState: number, // the state we want to toggle from
    toState: number, // the state we want to toggle to
  ) {
    const relevantCells: number[] = [];

    // collect cells that are either fromState or toState
    for (let i = 0; i < (isRow ? state.cols : state.rows); i++) {
      const row = isRow ? index : i;
      const col = isRow ? i : index;
      const cellIndex = row * state.cols + col;

      const current = state.board[cellIndex];
      if ([fromState, toState].includes(current)) relevantCells.push(cellIndex);
    }

    // Determine if any cell is in fromState
    const hasFromState = relevantCells.some((i) => state.board[i] === fromState);

    if (hasFromState) {
      // If any cell is in fromState, change only those to toState
      for (const i of relevantCells) if (state.board[i] === fromState) state.board[i] = toState;
      return;
    }

    // Otherwise, toggle all cells between toState and fromState
    for (const i of relevantCells) state.board[i] = state.board[i] === toState ? fromState : toState;
  }
}
