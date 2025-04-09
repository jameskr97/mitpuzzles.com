import type { PuzzleAdapter } from "@/store/game";
import { MinesweeperCellStates, type MinesweeperState } from "@/features/games/minesweeper/minesweeper.model";
import type { PuzzleKakurasu, PuzzleLightup, PuzzleMinesweeper, PuzzleSudoku, PuzzleTents } from "@/services/types";
import type { SudokuState } from "@/features/games/sudoku/sudoku.model";
import type { TentsState } from "@/features/games/tents/tents.model";
import { sha256 } from "@/services/util";
import { KakurasuCellStates, type KakurasuState } from "@/features/games/kakurasu/kakurasu.model";
import type { LightupState } from "@/features/games/lightup/lightup.model";

export const noopAdapter: PuzzleAdapter<{}, {}> = {
  normalize: (raw) => raw,
  empty_state: (raw) => raw,
  validate: async (_state, _raw) => false,
};

export const minesweeperAdapter: PuzzleAdapter<PuzzleMinesweeper, MinesweeperState> = {
  normalize: (raw) => ({
    rows: raw.rows,
    cols: raw.cols,
    board: raw.board.split("").map((ch) => {
      const map: Record<string, number> = { U: 10, F: 11, S: 12 };
      const n = parseInt(ch);
      return isNaN(n) ? map[ch] : n;
    }),
    gamestate: new Array(raw.rows * raw.cols).fill(MinesweeperCellStates.Unmarked),
    completed_at: null,
  }),

  empty_state: (raw) => ({
    rows: raw.rows,
    cols: raw.cols,
    board: raw.board.split("").map((ch) => {
      const map: Record<string, number> = { U: 10, F: 11, S: 12 };
      const n = parseInt(ch);
      return isNaN(n) ? map[ch] : n;
    }),
    gamestate: new Array(raw.rows * raw.cols).fill(MinesweeperCellStates.Unmarked),
    completed_at: null,
  }),

  validate: async (state, raw) => {
    const gamestate_hash = await sha256(state.gamestate.join(""));
    return gamestate_hash === raw.solution_hash;
  },
};

export const sudokuAdapter: PuzzleAdapter<PuzzleSudoku, SudokuState> = {
  normalize: (raw) => {
    const base_grid = [...raw.board].map((ch) => (ch === "-" ? 0 : Number(ch)));
    return {
      rows: raw.rows,
      cols: raw.cols,
      base_grid,
      user_grid: new Array(raw.rows * raw.cols).fill(0),
    };
  },

  empty_state: (raw) => {
    const base_grid = [...raw.board].map((ch) => (ch === "-" ? 0 : Number(ch)));
    return {
      rows: raw.rows,
      cols: raw.cols,
      base_grid,
      user_grid: new Array(raw.rows * raw.cols).fill(0),
    };
  },

  validate: (_state, _raw) => {
    return false;
  },
};

export const tentsAdapter: PuzzleAdapter<PuzzleTents, TentsState> = {
  normalize: (raw) => ({
    ...raw,
    trees: raw.trees.split("").map(Number),
    tents: new Array(raw.rows * raw.cols).fill(0),
  }),

  empty_state: (raw) => ({
    ...raw,
    trees: raw.trees.split("").map(Number),
    tents: new Array(raw.rows * raw.cols).fill(0),
  }),

  async validate(state, _raw): Promise<boolean> {
    const hash_current_state = await sha256(state.tents.join(""));
    return hash_current_state === state.solution_hash;
  },
};

export const kakurasuAdapter: PuzzleAdapter<PuzzleKakurasu, KakurasuState> = {
  normalize: (raw) => ({
    rows: raw.rows,
    cols: raw.cols,
    row_sum: raw.row_sum,
    col_sum: raw.col_sum,
    cell_black: new Array(raw.rows * raw.cols).fill(0),
  }),

  empty_state: (raw) => ({
    rows: raw.rows,
    cols: raw.cols,
    row_sum: raw.row_sum,
    col_sum: raw.col_sum,
    cell_black: new Array(raw.rows * raw.cols).fill(0),
  }),

  async validate(state, raw): Promise<boolean> {
    const board = state.cell_black
      .map((i) => {
        if (i === KakurasuCellStates.Filled) return "1";
        if (i === KakurasuCellStates.Empty) return "0";
        if (i === KakurasuCellStates.Crossed) return "0";
      })
      .join("");
    const hash_current_state = await sha256(board);
    return hash_current_state === raw.solution_hash;
  },
};

export const lightupAdapter: PuzzleAdapter<PuzzleLightup, LightupState> = {
  normalize: (raw) => {
    const walls: number[] = raw.board.split("").map((ch) => {
      const n = parseInt(ch);
      return isNaN(n) ? 9 : n;
    });

    return {
      ...raw,
      walls,
      bulbs: new Array(raw.cols * raw.rows).fill(0),
      lit: new Array(raw.cols * raw.rows).fill(0),
    };
  },

  empty_state: function (raw: PuzzleLightup) {
    return this.normalize(raw);
  },
  async validate(state, raw): Promise<boolean> {
    const hash_current_state = await sha256(state.bulbs.join(""));
    return hash_current_state === raw.solution_hash;
  },
};
