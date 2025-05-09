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
    cols: 7,
    rows: 7,
    col_sum: [4, 0, 14, 0, 7, 2, 6],
    row_sum: [0, 6, 3, 1, 3, 10, 5],
    board_initial: "0000000000000000000000000000000000000000000000000",
  },
  lightup: {
    rows: 7,
    cols: 7,
    board_initial: "..........20...2......5...5......1...35..........",
  },
  battleship: {
    rows: 6,
    cols: 6,
    row_counts: [2, 2, 3, 0, 3, 0],
    col_counts: [0, 3, 1, 3, 1, 2],
    // 0 = empty, 1 = water, 2 = ship
    board_initial:  "000000020000000000000000002000000000",
    board_solution_hash: "588daa36dcd2edcf163f14a094e7c136edc270ebd0299a89d243924b336adda2",
  },
};
