import type { GameKey } from "@/main";

/** * Default puzzles for each game type.
 *
 */
export const defaultPuzzles: Record<GameKey, any> = {
  minesweeper: { cols: 7, rows: 7, board: "U111U1112U222UUU2UUUU111121UU21UU11UU1113UU21UUUU" },
  sudoku: {
    cols: 9,
    rows: 9,
    board: "420069000008002095006030402063008170540973060080100509700204006834050901602090000",
  },
  tents: {
    rows: 6,
    cols: 6,
    row_counts: [2, 1, 1, 1, 1, 1],
    col_counts: [2, 0, 1, 1, 1, 2],
    trees: "010000000001000100000101000100010000",
    tents: "100001000100000001001000000010100000",
  },
  kakurasu: {
    cols: 4,
    rows: 4,
    row_sum: [6, 9, 4, 5],
    col_sum: [1, 7, 7, 5],
    cells_black: "1110011100010110",
  },
  lightup: {
    rows: 7,
    cols: 7,
    board: "..........20...2......5...5......1...35..........",
    solution: "0001000010000110010000000100001000001000100010000",
  },
};
