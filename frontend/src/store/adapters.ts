import { MinesweeperCellStates, type MinesweeperState } from "@/features/games/minesweeper/minesweeper.model";
import type { PuzzleKakurasu, PuzzleLightup, PuzzleMinesweeper, PuzzleSudoku, PuzzleTents } from "@/services/types";
import type { SudokuState } from "@/features/games/sudoku/sudoku.model";
import { TentCellStates, type TentsState } from "@/features/games/tents/tents.model";
import { sha256 } from "@/services/util";
import { KakurasuCellStates, type KakurasuState } from "@/features/games/kakurasu/kakurasu.model";
import type { LightupState } from "@/features/games/lightup/lightup.model";

/**
 * Adapter for converting raw board games to client-side board games,
 * and for validating games client-side.
 * @param Raw The raw payload from the backend
 * @param State The client-side structure
 */
export interface PuzzleAdapter<Raw, State = Raw> {
  /**
   * Convert the payload from the backend into the client-side structure
   * @param raw The raw payload from the backend
   */
  create_state(raw: Raw): State;

  /**
   * Validate the game board with the solution hash from the backend
   * or agains another solution
   * @param state The current state
   * @param raw The raw payload from the backend
   * @returns True if the game is solved, false otherwise
   */
  validate(state: State, raw: Raw): Promise<boolean> | boolean;

  /**
   * Check if the game can be validated.
   * We don't want the user to submit the game unless they have made all possible changes.
   * @param state
   * @param raw
   */
  can_validate(state: State, raw: Raw): boolean;
}

export const noopAdapter: PuzzleAdapter<{}, {}> = {
  create_state: (raw) => raw,
  validate: async (_state, _raw) => false,
  can_validate: (_state, _raw) => true,
};

export const minesweeperAdapter: PuzzleAdapter<PuzzleMinesweeper, MinesweeperState> = {
  create_state: (raw) => {
    const board = raw.board_initial.split("").map((ch) => {
      const map: Record<string, number> = { _: 10, F: 11, S: 12 };
      const n = parseInt(ch);
      return isNaN(n) ? map[ch] : n;
    });
    return {
      rows: raw.rows,
      cols: raw.cols,
      board,
      gamestate: new Array(raw.rows * raw.cols).fill(MinesweeperCellStates.Unmarked),
      completed_at: null,
    };
  },

  validate: async (state, raw) => {
    const converted = state.gamestate.map((cell, index) => {
      if (cell === 0) return raw.board_initial[index];
      if (cell === MinesweeperCellStates.Flagged) return "F";
      if (cell === MinesweeperCellStates.Safe) return "S";
      return cell;
    });

    const gamestate_hash = await sha256(converted.join(""));
    return gamestate_hash === raw.board_solution_hash;
  },

  can_validate: (state, raw) => {
    // can validate if all cells are either marked or unmarked
    return state.gamestate.every((cell, index) => {
      if (raw.board_initial[index] !== "_") return true; // initial cell is filled, so we can ignore it
      return cell !== MinesweeperCellStates.Unmarked; // user cell is filled
    });
  },
};

export const sudokuAdapter: PuzzleAdapter<PuzzleSudoku, SudokuState> = {
  create_state: (raw) => {
    const base_grid = raw.board_initial.split("").map(Number);
    return {
      rows: raw.rows,
      cols: raw.cols,
      base_grid,
      user_grid: new Array(raw.rows * raw.cols).fill(0),
    };
  },

  validate: async (state, raw) => {
    // apply user grid on top of base grid
    // take hash
    // compare result
    // const hash_current_state = await sha256(state.)
    const { base_grid, user_grid } = state;
    const final_grid = base_grid.map((val, i) => (val !== 0 ? val : user_grid[i]));
    const final_string = final_grid.join("");
    const hash = await sha256(final_string);
    return hash === raw.board_solution_hash;
  },
  can_validate: (state, raw) => {
    // can validate if all cells are either filled or empty
    const x = state.user_grid.every((cell, index) => {
      if (raw.board_initial[index] !== "0") return true; // initial cell is filled, so we can ignore it
      return cell !== 0; // user cell is filled
    });
    return x;
  },
};

export const tentsAdapter: PuzzleAdapter<PuzzleTents, TentsState> = {
  create_state: (raw) => {
    return {
      ...raw,
      trees: raw.board_initial.split("").map(Number),
      cell_states: new Array(raw.rows * raw.cols).fill(0),
    };
  },

  async validate(state, _raw): Promise<boolean> {
    // ensure no cell_state (that doesn't match a tree position) is marked as empty
    if (state.cell_states.some((cell, index) => cell === TentCellStates.Empty && state.trees[index] !== 1))
      return false;

    const board = state.cell_states
      .map((cell, index) => {
        if (state.trees[index] === 1) return "1"; // tree
        if (cell === TentCellStates.Tent) return "2";
        if (cell === TentCellStates.Green) return "3";
      })
      .join("");
    const hash_current_state = await sha256(board);
    return hash_current_state === state.board_solution_hash;
  },

  can_validate: (state, raw) => {
    // can validate if all cells are either filled or empty
    return state.cell_states.every((cell, index) => {
      if (raw.board_initial[index] !== "0") return true; // initial cell is filled, so we can ignore it
      return cell !== TentCellStates.Empty; // user cell is filled
    });
  },
};

export const kakurasuAdapter: PuzzleAdapter<PuzzleKakurasu, KakurasuState> = {
  create_state: (raw) => ({
    rows: raw.rows,
    cols: raw.cols,
    row_sum: raw.row_sum,
    col_sum: raw.col_sum,
    cell_black: new Array(raw.rows * raw.cols).fill(0),
  }),

  async validate(state, raw): Promise<boolean> {
    if (state.cell_black.some((i) => i === KakurasuCellStates.Empty)) return false;

    const board = state.cell_black
      .map((i) => {
        if (i === KakurasuCellStates.Filled) return "1";
        if (i === KakurasuCellStates.Empty) return "0";
        if (i === KakurasuCellStates.Crossed) return "0";
      })
      .join("");
    const hash_current_state = await sha256(board);
    return hash_current_state === raw.board_solution_hash;
  },

  can_validate: (state, raw) => {
    // can validate if all cells are either filled or empty
    return state.cell_black.every((cell, index) => {
      if (raw.board_initial[index] !== "0") return true; // initial cell is filled, so we can ignore it
      return cell !== KakurasuCellStates.Empty; // user cell is filled
    });
  },
};

export const lightupAdapter: PuzzleAdapter<PuzzleLightup, LightupState> = {
  create_state: (raw) => {
    const walls: number[] = raw.board_initial.split("").map((ch) => {
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

  async validate(state, raw): Promise<boolean> {
    const board = raw.board_initial
      .split("")
      .map((cell, index) => {
        if (cell !== ".") return cell;
        return state.bulbs[index] === 1 ? "L" : "0";
      })
      .join("");
    const hash_current_state = await sha256(board);
    return hash_current_state === raw.board_solution_hash;
  },
  can_validate: (_state, _raw) => true,
};
