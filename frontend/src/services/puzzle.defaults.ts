import type { GameKey } from "@/main";

/** * Default puzzles for each game type.
 *
 */
export const defaultPuzzles: Record<GameKey, any> = {
  minesweeper: { cols: 7, rows: 7, board_initial: "_111_1112_222___2____111121__21__11__1113__21____" },
  sudoku: {
    cols: 9,
    rows: 9,
    board_initial: "420069000008002095006030402063008170540973060080100509700204006834050901602090000",
  },
  tents: {
    rows: 6,
    cols: 6,
    row_counts: [2, 1, 1, 1, 1, 1],
    col_counts: [2, 0, 1, 1, 1, 2],
    board_initial: "010000000001000100000101000100010000",
  },
  kakurasu: {
    cols: 4,
    rows: 4,
    row_sum: [6, 9, 4, 5],
    col_sum: [1, 7, 7, 5],
    board_initial: "1110011100010110",
  },
  lightup: {
    rows: 7,
    cols: 7,
    board_initial: "..........20...2......5...5......1...35..........",
  },
};
