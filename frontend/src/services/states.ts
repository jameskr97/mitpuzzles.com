export interface MutablePuzzleState {
  cols: number;
  rows: number;
  board: number[];
}
export type MutablePuzzleStateExtended<T extends object = {}> = MutablePuzzleState & T;

export type PuzzleStateKakurasu = MutablePuzzleStateExtended<{
  board_initial: number[];
  col_sum: number[];
  row_sum: number[];
}>;

export type PuzzleStateTents = MutablePuzzleStateExtended<{
  row_counts: number[];
  col_counts: number[];
}>;

export type PuzzleStateSudoku = MutablePuzzleStateExtended<{
  active_cell?: [number, number];
  board_initial: string;
}>;

export type PuzzleStateLightup = MutablePuzzleStateExtended<{
  lit: boolean[];
}>;

export type PuzzleStateMinesweeper = MutablePuzzleStateExtended<{
  board_initial: string;
}>;

export type PuzzleStateBattleship = MutablePuzzleStateExtended<{
  board_initial: string;
  row_counts: number[];
  col_counts: number[];
}>;

export type PuzzleStateNonograms = MutablePuzzleStateExtended<{
  col_sum: number[];
  row_sum: number[];
}>;

