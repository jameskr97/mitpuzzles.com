export interface MutablePuzzleState {
  cols: number;
  rows: number;
  board: number[];
  immutable: number[]; // Immutable cells (1 for immutable, 0 for mutable)
  tutorial_mode: boolean; // Whether the puzzle is in tutorial mode
  session_id: string;
  puzzle_type: string;
  puzzle_size: string;
  puzzle_difficulty: string;
  violations: GameViolation[];
  solved: boolean;
}

export interface GameViolation {
  rule_type: string;
  locations: { row: number; col: number }[]; // Array of [row, col] pairs where the violation occurred
}

export type MutablePuzzleStateExtended<T extends object = {}> = MutablePuzzleState & T;

export type PuzzleStateKakurasu = MutablePuzzleStateExtended<{
  col_sums: number[];
  row_sums: number[];
}>;

export type PuzzleStateTents = MutablePuzzleStateExtended<{
  row_counts: number[];
  col_counts: number[];
}>;

export type PuzzleStateSudoku = MutablePuzzleStateExtended<{
  board_initial: number[];
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
  row_sum: number[];
  col_sum: number[];
}>;

export type AnyPuzzleState =
  | PuzzleStateKakurasu
  | PuzzleStateTents
  | PuzzleStateSudoku
  | PuzzleStateLightup
  | PuzzleStateMinesweeper
  | PuzzleStateBattleship
  | PuzzleStateNonograms;
