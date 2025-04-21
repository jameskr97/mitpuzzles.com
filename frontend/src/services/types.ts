export interface PuzzleMinesweeper {
  id: number;
  cols: number;
  rows: number;
  board_initial: string;
  board_solution_hash: string;
}

export interface PuzzleSudoku {
  id: number;
  cols: number;
  rows: number;
  board_initial: string;
  board_solution_hash: string;
}

export interface PuzzleTents {
  id: number;
  cols: number;
  rows: number;
  trees: string;
  row_counts: number[];
  col_counts: number[];
  board_initial: string;
  board_solution_hash: string;
}

export interface PuzzleKakurasu {
  id: number;
  cols: number;
  rows: number;
  row_sum: number[];
  col_sum: number[];
  board_initial: string;
  board_solution_hash: string;
}

export interface PuzzleLightup {
  id: number;
  cols: number;
  rows: number;
  board_initial: string;
  board_solution_hash: string;
}
