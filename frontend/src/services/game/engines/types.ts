import { type Ref } from "vue";
import type { Cell } from "@/features/games.components/board.interaction.ts";
import type { PuzzleEngine, RuleViolation } from "@/services/game/engines/PuzzleEngine.ts";

export interface PuzzleDefinition<T = {}> {
  id: number;
  puzzle_type: string;
  rows: number;
  cols: number;
  initial_state: number[][];
  solution_hash: string;
  meta: T;
}

export type KakurasuMeta = {
  col_sums: number[];
  row_sums: number[];
};

export type TentsMeta = {
  row_tent_counts: number[];
  col_tent_counts: number[];
};

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

  // game actions
  handle_cell_click: (cell: Cell, event: MouseEvent, override?: number) => void;
  handle_cell_key_down: (cell: Cell, event: KeyboardEvent, key: string | number) => void;

  // puzzle actions
  request_new_puzzle: () => void | Promise<void>;
  clear_puzzle: () => void;
  check_solution: () => void;
}
