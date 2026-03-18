/**
 * useAquariumGame - Core game logic for Aquarium
 *
 * Mode-agnostic: works in both freeplay and experiment contexts.
 *
 * Rules:
 * - Grid is divided into irregular regions (aquariums/tanks)
 * - Numbers along top indicate how many cells in each column should be filled with water
 * - Numbers along left indicate how many cells in each row should be filled with water
 * - Water obeys gravity: if a cell is filled, all cells below it in the same region must also be filled
 * - Different aquariums are independent (water level can differ between tanks)
 */
import { type ComputedRef, type Ref } from "vue";
import {
  useBoardState,
  useStateCycler,
  useSolutionChecker,
  count_in_row,
  count_in_col,
  get_region_at,
  same_region as same_region_util,
} from "@/core/games/composables";
import type { PuzzleDefinition, RuleViolation } from "@/core/games/types/puzzle-types.ts";

/**
 * Aquarium cell values
 */
export const AquariumCell = {
  EMPTY: -1,
  WATER: -3,
  CROSS: -4,
} as const;

export type AquariumCellValue = (typeof AquariumCell)[keyof typeof AquariumCell];

export interface AquariumMeta {
  regions: number[][];
  row_hints: number[];
  col_hints: number[];
}

export interface AquariumGameReturn {
  board: Ref<number[][]>;
  initial_state: Readonly<number[][]>;
  rows: ComputedRef<number>;
  cols: ComputedRef<number>;
  region_map: number[][];
  handle_cell_click: (row: number, col: number, button: number) => { old_value: number; new_value: number } | null;
  set_cell_value: (row: number, col: number, value: number) => { old_value: number; new_value: number } | null;
  handle_line_toggle: (is_row: boolean, index: number, from_state: number, to_state: number) => { changes: Array<{ row: number; col: number; old_value: number; new_value: number }> };
  check_solution: () => Promise<boolean>;
  clear: () => void;
  get_violations: () => RuleViolation[];
  /** Get region ID for a cell */
  get_region: (row: number, col: number) => number;
  /** Check if two adjacent cells are in the same region */
  same_region: (r1: number, c1: number, r2: number, c2: number) => boolean;
  definition: PuzzleDefinition<AquariumMeta>;
}

/**
 * Create Aquarium game logic
 */
export function useAquariumGame(
  definition: PuzzleDefinition<AquariumMeta>,
  saved_board?: number[][] | null
): AquariumGameReturn {
  const region_map = definition.meta?.regions || [];

  // Initialize board with EMPTY cells
  const initial_board = definition.initial_state.map((row) =>
    row.map(() => AquariumCell.EMPTY)
  );

  const {
    board,
    initial_state,
    rows,
    cols,
    set_cell,
    get_cell,
    clear,
    is_cell_editable,
  } = useBoardState(initial_board, saved_board, {
    is_editable: () => true,
  });

  const { cycle_state } = useStateCycler([
    AquariumCell.EMPTY,
    AquariumCell.WATER,
    AquariumCell.CROSS,
  ]);

  const solution_checker = useSolutionChecker({
    type: "cell-grid",
    solution_hash: definition.solution_hash,
    positive_values: [AquariumCell.WATER],
  });

  function get_region(row: number, col: number): number {
    return get_region_at(region_map, row, col);
  }

  function same_region(r1: number, c1: number, r2: number, c2: number): boolean {
    return same_region_util(region_map, r1, c1, r2, c2);
  }

  function handle_cell_click(row: number, col: number, button: number) {
    if (!is_cell_editable(row, col)) return null;
    const old_value = get_cell(row, col);
    const new_value = cycle_state(old_value, button);
    set_cell(row, col, new_value);
    return { old_value, new_value };
  }

  function set_cell_value(row: number, col: number, value: number) {
    if (!is_cell_editable(row, col)) return null;
    const old_value = get_cell(row, col);
    if (old_value === value) return null;
    set_cell(row, col, value);
    return { old_value, new_value: value };
  }

  /**
   * Check gravity violation: if a cell is filled, all cells below it in the same region must be filled
   */
  function check_gravity_violation(row: number, col: number): boolean {
    const state = board.value;
    const cell_region = get_region(row, col);

    // If this cell is not water, no gravity violation
    if (state[row][col] !== AquariumCell.WATER) return false;

    // Check all cells below in the same region
    for (let r = row + 1; r < rows.value; r++) {
      if (get_region(r, col) === cell_region) {
        // Cell below in same region must be water
        if (state[r][col] !== AquariumCell.WATER) {
          return true;
        }
      }
    }
    return false;
  }

  function get_violations(): RuleViolation[] {
    const violations: RuleViolation[] = [];
    const state = board.value;
    const meta = definition.meta!;

    // Check gravity violations
    for (let r = 0; r < rows.value; r++) {
      for (let c = 0; c < cols.value; c++) {
        if (check_gravity_violation(r, c)) {
          violations.push({
            rule_name: "aquarium_gravity_violation",
            locations: [{ row: r, col: c }],
          });
        }
      }
    }

    // Check row hints (count water in each row)
    for (let r = 0; r < rows.value; r++) {
      const water_count = count_in_row(state, r, [AquariumCell.WATER]);
      if (water_count > meta.row_hints[r]) {
        violations.push({
          rule_name: "aquarium_row_exceeded",
          locations: [{ row: r, col: -1 }],
        });
      }
    }

    // Check column hints (count water in each column)
    for (let c = 0; c < cols.value; c++) {
      const water_count = count_in_col(state, c, [AquariumCell.WATER]);
      if (water_count > meta.col_hints[c]) {
        violations.push({
          rule_name: "aquarium_col_exceeded",
          locations: [{ row: -1, col: c }],
        });
      }
    }

    return violations;
  }

  function handle_line_toggle(
    is_row: boolean,
    index: number,
    from_state: number,
    to_state: number
  ): { changes: Array<{ row: number; col: number; old_value: number; new_value: number }> } {
    const changes: Array<{ row: number; col: number; old_value: number; new_value: number }> = [];
    const length = is_row ? cols.value : rows.value;

    const cells: Array<{ row: number; col: number; value: number }> = [];
    for (let i = 0; i < length; i++) {
      const row = is_row ? index : i;
      const col = is_row ? i : index;
      if (!is_cell_editable(row, col)) continue;
      cells.push({ row, col, value: get_cell(row, col) });
    }

    const has_empty = cells.some((c) => c.value === from_state);

    if (has_empty) {
      for (const { row, col, value } of cells) {
        if (value === from_state) {
          set_cell(row, col, to_state);
          changes.push({ row, col, old_value: value, new_value: to_state });
        }
      }
    } else {
      for (const { row, col, value } of cells) {
        if (value === to_state) {
          set_cell(row, col, from_state);
          changes.push({ row, col, old_value: value, new_value: from_state });
        }
      }
    }

    return { changes };
  }

  return {
    board,
    initial_state,
    rows,
    cols,
    region_map,
    handle_cell_click,
    set_cell_value,
    handle_line_toggle,
    check_solution: () => solution_checker.check(board.value),
    clear,
    get_violations,
    get_region,
    same_region,
    definition,
  };
}
