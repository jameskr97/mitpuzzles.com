import type { PUZZLE_TYPES } from "@/constants";
import type { PuzzleState } from "@/services/game/engines/types.ts";

export const defaultPuzzles: Record<PUZZLE_TYPES, PuzzleState> = {
  minesweeper: {
    // @ts-expect-error intentionally incomplete
    definition: {
      cols: 7,
      rows: 7,
    },
    board: [
      [0, 1, 1, 1, 0, 1, 1],
      [1, 2, 0, 2, 2, 2, 0],
      [0, 0, 2, 0, 0, 0, 0],
      [1, 1, 1, 1, 2, 1, 0],
      [0, 2, 1, 0, 0, 1, 1],
      [0, 0, 1, 1, 1, 3, 0],
      [0, 2, 1, 0, 0, 0, 0],
    ],
  },
  sudoku: {
    // @ts-expect-error intentionally incomplete
    definition: {
      cols: 9,
      rows: 9,
      initial_state: [
        [4, 4, 0, 0, 6, 9, 0, 0, 0],
        [0, 0, 8, 0, 0, 2, 0, 9, 5],
        [0, 0, 6, 0, 3, 0, 4, 0, 2],
        [0, 6, 3, 0, 0, 8, 1, 7, 0],
        [5, 4, 0, 9, 7, 3, 0, 6, 0],
        [0, 8, 0, 1, 0, 0, 5, 0, 9],
        [7, 0, 0, 2, 0, 4, 0, 0, 6],
        [8, 3, 4, 0, 5, 0, 9, 0, 1],
        [6, 0, 2, 0, 9, 0, 0, 0, 0],
      ],
    },
    board: [
      [4, 4, 0, 0, 6, 9, 0, 0, 0],
      [0, 0, 8, 0, 0, 2, 0, 9, 5],
      [0, 0, 6, 0, 3, 0, 4, 0, 2],
      [0, 6, 3, 0, 0, 8, 1, 7, 0],
      [5, 4, 0, 9, 7, 3, 0, 6, 0],
      [0, 8, 0, 1, 0, 0, 5, 0, 9],
      [7, 0, 0, 2, 0, 4, 0, 0, 6],
      [8, 3, 4, 0, 5, 0, 9, 0, 1],
      [6, 0, 2, 0, 9, 0, 0, 0, 0],
    ],
  },
  tents: {
    // @ts-expect-error intentionally incomplete
    definition: {
      rows: 6,
      cols: 6,
      meta: {
        row_tent_counts: [2, 1, 1, 1, 1, 1],
        col_tent_counts: [2, 0, 1, 1, 1, 2],
      },
    },
    board: [
      [0, 1, 0, 0, 0, 0],
      [0, 0, 0, 0, 0, 1],
      [0, 0, 0, 1, 0, 0],
      [0, 0, 0, 1, 0, 1],
      [0, 0, 0, 1, 0, 0],
      [0, 1, 0, 0, 0, 0],
    ],
    solved: false,
    immutable_cells: [
      [0, 0, 0, 0, 0, 0],
      [0, 0, 0, 0, 0, 0],
      [0, 0, 0, 0, 0, 0],
      [0, 0, 0, 0, 0, 0],
      [0, 0, 0, 0, 0, 0],
      [0, 0, 0, 0, 0, 0],
    ],
    violations: [],
  },
  kakurasu: {
    // @ts-expect-error intentionally incomplete
    definition: {
      cols: 7,
      rows: 7,
      meta: {
        col_sums: [4, 0, 14, 0, 7, 2, 6],
        row_sums: [0, 6, 3, 1, 3, 10, 5],
      },
    },
    board: [
      [0, 0, 0, 0, 0, 0, 0],
      [0, 0, 0, 0, 0, 0, 0],
      [0, 0, 0, 0, 0, 0, 0],
      [0, 0, 0, 0, 0, 0, 0],
      [0, 0, 0, 0, 0, 0, 0],
      [0, 0, 0, 0, 0, 0, 0],
      [0, 0, 0, 0, 0, 0, 0],
    ],
  },
  lightup: {
    // @ts-expect-error intentionally incomplete
    definition: {
      rows: 7,
      cols: 7,
    },
    board: [
      [6, 6, 6, 6, 6, 6, 6],
      [6, 6, 6, 2, 0, 6, 6],
      [6, 2, 6, 6, 6, 6, 6],
      [6, 6, 5, 6, 6, 6, 5],
      [6, 6, 6, 1, 6, 6, 6],
      [6, 3, 5, 6, 6, 6, 6],
      [6, 6, 6, 6, 6, 6, 6],
    ],
  },
  battleships: {
    // @ts-expect-error intentionally incomplete
    definition: {
      rows: 6,
      cols: 6,
      meta: {
        row_sums: [2, 2, 3, 0, 3, 0],
        col_sums: [0, 3, 1, 3, 1, 2],
      },
      initial_state: [
        [0, 0, 0, 0, 0, 0],
        [0, 2, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 2, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
      ],
    },
    board: [
      [0, 0, 0, 0, 0, 0],
      [0, 0, 0, 0, 0, 0],
      [0, 0, 0, 0, 0, 0],
      [0, 0, 0, 0, 0, 0],
      [0, 0, 0, 0, 0, 0],
      [0, 0, 0, 0, 0, 0],
    ],
  },
  nonograms: {
    // @ts-expect-error intentionally incomplete
    definition: {
      rows: 5,
      cols: 5,
      meta: {
        row_hints: [[3], [1], [1, 2], [1, 2], [1, 2]],
        col_hints: [[2], [1, 3], [1], [3], [3]],
      },
    },
    board: [
      [0, 0, 0, 0, 0],
      [0, 0, 0, 0, 0],
      [0, 0, 0, 0, 0],
      [0, 0, 0, 0, 0],
      [0, 0, 0, 0, 0],
    ],
  },
};
