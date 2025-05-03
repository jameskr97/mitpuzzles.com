/**
 * This file should match 1-to-1 with the backend serializers.
 * PuzzleRecord == PuzzleBaseSerializer
 * PuzzleRecordMinesweeper == PuzzleMinesweeperSerializer
 */

/**
 * This is the base response of data that is returned from the server.
 */
export interface PuzzleRecord {
  id: number;
  cols: number;
  rows: number;
  board_initial: string;
  board_solution_hash: string;
}
export type PuzzleRecordExtended<T extends object = {}> = PuzzleRecord & T;

export type PuzzleRecordMinesweeper = PuzzleRecord;
export type PuzzleRecordSudoku = PuzzleRecord;
export type PuzzleRecordLightup = PuzzleRecord;

export type PuzzleRecordTents = PuzzleRecordExtended<{
  trees: string;
  row_counts: number[];
  col_counts: number[];
}>;

export type PuzzleRecordKakurasu = PuzzleRecordExtended<{
  row_sum: number[];
  col_sum: number[];
}>;
