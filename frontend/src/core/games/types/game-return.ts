

import type { PuzzleDefinition, RuleViolation } from "@/core/games/types/puzzle-types.ts";
import type { Ref, ComputedRef } from "vue";

// message types
export interface CellChangeResult {
  old_value: number;
  new_value: number;
}

export interface LineToggleResult {
  changes: Array<{ row: number; col: number; old_value: number; new_value: number }>;
}

// here are the properties that every game returns (grid or otherwise)
export interface BaseGameReturn<GameType = any>{
  definition: PuzzleDefinition<GameType>,
  check_solution: () => Promise<boolean>,
  clear: () => void,
}

// here are the properties that all grid games return
export interface GridGameReturn<GameType = any> extends BaseGameReturn<GameType> {
  board: Ref<number[][]>;
  initial_state: Readonly<number[][]>;
  rows: ComputedRef<number>;
  cols: ComputedRef<number>;
  get_violations: () => RuleViolation[];
  set_cell_value: (row: number, col: number, value: number) => CellChangeResult | null;
  immutable_cells?: ComputedRef<number[][]>;
  handle_cell_click?: (row: number, col: number, button: number) => CellChangeResult | null;
  handle_line_toggle?: (is_row: boolean, index: number, from_state: number, to_state: number) => LineToggleResult;
}
