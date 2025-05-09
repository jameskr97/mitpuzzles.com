import type { MutablePuzzleState } from "@/services/states.ts";

export class PuzzleModelOps {
  static changeRowState(row: number, state: MutablePuzzleState, fromState: number, toState: number) {
    for (let col = 0; col < state.cols; col++) {
      const i = row * state.cols + col;
      if (state.board[i] === fromState) {
        state.board[i] = toState;
      } else if (state.board[i] === toState) {
        state.board[i] = fromState;
      }
    }
  }

  static changeColState(col: number, state: MutablePuzzleState, fromState: number, toState: number) {
    for (let row = 0; row < state.rows; row++) {
      const i = row * state.cols + col;
      if (state.board[i] === fromState) {
        state.board[i] = toState;
      } else if (state.board[i] === toState) {
        state.board[i] = fromState;
      }
    }
  }
}
