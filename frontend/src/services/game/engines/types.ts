import { type Ref } from "vue";
import type { Cell } from "@/features/games.components/board.interaction.ts";
import type { RuleViolation } from "@/services/game/engines/PuzzleEngine.ts";

export interface PuzzleDefinition<T = {}> {
  id: string;
  puzzle_type: string;
  rows: number;
  cols: number;
  initial_state: number[][];
  solution?: number[][];
  solution_hash?: string;
  meta?: T;
}

export type KakurasuMeta = {
  col_sums: number[];
  row_sums: number[];
};

export type TentsMeta = {
  row_tent_counts: number[];
  col_tent_counts: number[];
  count_tents: number;
};

export type BattleshipsMeta = {
  col_sums: number[];
  row_sums: number[];
  ships_dict: Record<string, number>,
};

export type NonogramMeta = {
  row_hints: number[][];
  col_hints: number[][];
  count_black_cells: number;
}

export type PuzzleState<T = any> = {
  definition: PuzzleDefinition<T>;
  board: number[][];
  solved: boolean;
  immutable_cells: number[][];
  violations: Array<RuleViolation>;
};

export interface PuzzleUIState {
  tutorial_mode: boolean;
  show_solved_state: boolean;
  show_violations: boolean;
  animate_success: boolean;
  animate_failure: boolean;
}

export interface PuzzleController<TMeta = any> {
  state_puzzle: Ref<PuzzleState<TMeta>>;
  state_ui: Ref<PuzzleUIState>;
  current_puzzle_variant?: Ref<string[]>;

  // game actions
  handle_cell_click: (cell: Cell, event: MouseEvent, override?: number) => void;
  handle_cell_key_down: (cell: Cell, event: KeyboardEvent, key: string | number) => void;
  handle_cell_focus?: (cell: Cell, event: MouseEvent) => void;
  handle_hover_start?: (cell: Cell, event: MouseEvent) => void;
  handle_hover_end?: (cell: Cell, event: MouseEvent) => void;

  // metadata getters
  get_incorrect_cells?: () => { row: number; col: number }[];
  get_correct_cells?: () => { row: number; col: number }[];

  // puzzle actions
  request_new_puzzle: () => void | Promise<void>;
  clear_puzzle: () => void;
  check_solution: () => boolean | Promise<boolean>;
}
