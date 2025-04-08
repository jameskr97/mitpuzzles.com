export interface PuzzleMinesweeper {
  id: number;
  cols: number;
  rows: number;
  board: string;
  solution_hash: string;
}

export interface PuzzleSudoku {
  id: number;
  cols: number;
  rows: number;
  board: string;
}

export interface PuzzleTents {
  id: number;
  cols: number;
  rows: number;
  trees: string;
  row_counts: number[];
  col_counts: number[];
  solution_hash: string;
}
