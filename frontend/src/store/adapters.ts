import { sha256 } from "@/services/util";
import type {
  PuzzleStateKakurasu,
  PuzzleStateLightup,
  PuzzleStateMinesweeper,
  PuzzleStateSudoku,
  PuzzleStateTents,
} from "@/services/states.ts";
import type {
  PuzzleRecordKakurasu,
  PuzzleRecordLightup,
  PuzzleRecordMinesweeper,
  PuzzleRecordSudoku,
  PuzzleRecordTents,
} from "@/services/types.ts";
import { MinesweeperCellStates } from "@/features/games/minesweeper/minesweeper.model.ts";
import { TentCellStates } from "@/features/games/tents/tents.model.ts";
import { KakurasuCellStates } from "@/features/games/kakurasu/kakurasu.model.ts";
import { LightupCellStates } from "@/features/games/lightup/lightup.model.ts";

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

export const minesweeperAdapter: PuzzleAdapter<PuzzleRecordMinesweeper, PuzzleStateMinesweeper> = {
  create_state: (raw) => {
    const board = raw.board_initial.split("").map((ch) => {
      const map: Record<string, number> = { _: 10, F: 11, S: 12 };
      const n = parseInt(ch);
      return isNaN(n) ? map[ch] : n;
    });
    return {
      rows: raw.rows,
      cols: raw.cols,
      board_initial: raw.board_initial,
      board,
    };
  },

  validate: async (state, raw) => {
    const converted = state.board.map((cell, index) => {
      if (raw.board_initial[index] !== "_") return raw.board_initial[index]; // initial cell is filled, so we can ignore it
      if (cell === MinesweeperCellStates.Flagged) return "F";
      if (cell === MinesweeperCellStates.Safe) return "S";
      return cell;
    });

    const gamestate_hash = await sha256(converted.join(""));
    return gamestate_hash === raw.board_solution_hash;
  },

  can_validate: (_state, _raw) => {
    return true;
    // can validate if all cells are either marked or unmarked
    // return state.board.every((cell, index) => {
    //   if (raw.board_initial[index] !== "_") return true; // initial cell is filled, so we can ignore it
    //   return cell !== MinesweeperCellStates.Unmarked; // user cell is filled
    // });
  },
};

export const sudokuAdapter: PuzzleAdapter<PuzzleRecordSudoku, PuzzleStateSudoku> = {
  create_state: (raw) => ({
    rows: raw.rows,
    cols: raw.cols,
    board: new Array(raw.rows * raw.cols).fill(0),
    board_initial: raw.board_initial,
    active_cell: undefined,
  }),

  validate: async (state, raw) => {
    const final_grid = state.board_initial
      .split("")
      .map((val, i) => Number(val !== "0" ? val : state.board[i]))
      .join("");
    const hash = await sha256(final_grid);
    return hash === raw.board_solution_hash;
  },
  can_validate: (_state, _raw) => {
    return true;
    // const final_grid = state.board_initial.split("").map((val, i) => Number(val !== "0" ? val : state.board[i]));
    // return !final_grid.some((cell) => cell === 0);
  },
};

export const tentsAdapter: PuzzleAdapter<PuzzleRecordTents, PuzzleStateTents> = {
  create_state: (raw) => {
    return {
      ...raw,
      board: raw.board_initial.split("").map(Number),
    };
  },

  async validate(state, raw): Promise<boolean> {
    // ensure no cell_state (that doesn't match a tree position) is marked as empty
    if (state.board.some((cell) => cell === TentCellStates.Empty)) return false;

    const board = state.board.join("");
    const hash_current_state = await sha256(board);
    return hash_current_state === raw.board_solution_hash;
  },

  can_validate: (_state, _raw) => {
    return true;
    // return !state.board.some((cell) => cell === TentCellStates.Empty);
  },
};

export const kakurasuAdapter: PuzzleAdapter<PuzzleRecordKakurasu, PuzzleStateKakurasu> = {
  create_state: (raw) => ({
    rows: raw.rows,
    cols: raw.cols,
    row_sum: raw.row_sum,
    col_sum: raw.col_sum,
    board: raw.board_initial.split("").map(Number),
  }),

  async validate(state, raw): Promise<boolean> {
    const board = state.board
      .map((i) => {
        if (i === KakurasuCellStates.Filled) return "1";
        if (i === KakurasuCellStates.Empty) return "0";
        if (i === KakurasuCellStates.Crossed) return "0";
      })
      .join("");
    const hash_current_state = await sha256(board);
    return hash_current_state === raw.board_solution_hash;
  },

  can_validate: (_state, _raw) => {
    // can validate if all cells are either filled or empty
    // return state.cell_black.every((cell, index) => {
    //   if (raw.board_initial[index] !== "0") return true; // initial cell is filled, so we can ignore it
    //   return cell !== KakurasuCellStates.Empty; // user cell is filled
    // });
    return true;
  },
};

export const lightupAdapter: PuzzleAdapter<PuzzleRecordLightup, PuzzleStateLightup> = {
  create_state: (raw) => {
    const board = raw.board_initial
      .split("")
      .map(Number)
      .map((cell) => (isNaN(cell) ? LightupCellStates.Empty : cell));

    return {
      rows: raw.rows,
      cols: raw.cols,
      board,
      lit: new Array(raw.rows * raw.cols).fill(0),
    };
  },

  async validate(state, raw): Promise<boolean> {
    const board = raw.board_initial
      .split("")
      .map((cell, index) => {
        if (cell !== ".") return cell;
        return state.board[index] === LightupCellStates.Bulb ? "L" : "0";
      })
      .join("");
    const hash_current_state = await sha256(board);
    return hash_current_state === raw.board_solution_hash;
  },
  can_validate: (_state, _raw) => true,
};
