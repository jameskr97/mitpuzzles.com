/**
 * useKakurasuGame - Core game logic for Kakurasu
 *
 * Mode-agnostic: works in both freeplay and experiment contexts.
 * Uses the new game primitives architecture.
 */
import { type ComputedRef, type Ref } from "vue";
import {
  useBoardState,
  useStateCycler,
  useSolutionChecker,
  weighted_sum_row,
  weighted_sum_col,
  all_cells_in_row,
  all_cells_in_col,
} from "@/core/games/composables";
import type { PuzzleDefinition, KakurasuMeta, RuleViolation } from "@/core/games/types/puzzle-types.ts";

/**
 * Kakurasu cell values (research format)
 */
export const KakurasuCell = {
  EMPTY: -1,
  BLACK: 1,
  CROSS: 0,
} as const;

export type KakurasuCellValue = (typeof KakurasuCell)[keyof typeof KakurasuCell];

export interface KakurasuGameReturn {
  /** Current board state */
  board: Ref<number[][]>;

  /** Initial state for reference */
  initial_state: Readonly<number[][]>;

  /** Number of rows */
  rows: ComputedRef<number>;

  /** Number of columns */
  cols: ComputedRef<number>;

  /** Immutable cells matrix (all cells editable in Kakurasu) */
  immutable_cells: ComputedRef<number[][]>;

  /** Handle cell click - returns old/new values for recording */
  handle_cell_click: (
    row: number,
    col: number,
    button: number
  ) => { old_value: number; new_value: number } | null;

  /** Set cell to specific value (for drag operations) */
  set_cell_value: (
    row: number,
    col: number,
    value: number
  ) => { old_value: number; new_value: number } | null;

  /** Check solution */
  check_solution: () => Promise<boolean>;

  /** Clear board */
  clear: () => void;

  /** Get rule violations */
  get_violations: () => RuleViolation[];

  /** Toggle all cells in a row/column between two states */
  handle_line_toggle: (
    is_row: boolean,
    index: number,
    from_state: number,
    to_state: number
  ) => { changes: Array<{ row: number; col: number; old_value: number; new_value: number }> };

  /** Puzzle definition */
  definition: PuzzleDefinition<KakurasuMeta>;
}

/**
 * Create Kakurasu game logic
 */
export function useKakurasuGame(
  definition: PuzzleDefinition<KakurasuMeta>,
  saved_board?: number[][] | null
): KakurasuGameReturn {
  // Board state management - all cells are editable in Kakurasu
  // Uses research format directly (no conversion needed)
  const {
    board,
    initial_state,
    rows,
    cols,
    set_cell,
    get_cell,
    clear,
    is_cell_editable,
    immutable_cells,
  } = useBoardState(definition.initial_state, saved_board ?? null, {
    is_editable: () => true, // All cells are editable
  });

  // State cycler for click behavior
  const { cycle_state } = useStateCycler([
    KakurasuCell.EMPTY,
    KakurasuCell.BLACK,
    KakurasuCell.CROSS,
  ]);

  // Solution checker
  const solution_checker = useSolutionChecker({
    type: "cell-grid",
    solution_hash: definition.solution_hash,
    positive_values: [KakurasuCell.BLACK],
  });

  /**
   * Handle cell click
   */
  function handle_cell_click(
    row: number,
    col: number,
    button: number
  ): { old_value: number; new_value: number } | null {
    if (!is_cell_editable(row, col)) {
      return null;
    }

    const old_value = get_cell(row, col);
    const new_value = cycle_state(old_value, button);
    set_cell(row, col, new_value);

    return { old_value, new_value };
  }

  /**
   * Set cell to specific value (for drag operations)
   */
  function set_cell_value(
    row: number,
    col: number,
    value: number
  ): { old_value: number; new_value: number } | null {
    if (!is_cell_editable(row, col)) {
      return null;
    }

    const old_value = get_cell(row, col);
    if (old_value === value) {
      return null;
    }

    set_cell(row, col, value);
    return { old_value, new_value: value };
  }

  /**
   * Get rule violations (line sum exceeded)
   */
  function get_violations(): RuleViolation[] {
    const violations: RuleViolation[] = [];
    const state = board.value;
    const meta = definition.meta!;

    // Check row sums
    for (let r = 0; r < rows.value; r++) {
      const row_sum = weighted_sum_row(state, r, [KakurasuCell.BLACK]);

      if (row_sum > meta.row_sums[r]) {
        violations.push({
          rule_name: "line_sum_row_exceeded",
          locations: [{ row: r, col: -1 }],
        });
      }

      if (all_cells_in_row(state, r, [KakurasuCell.CROSS]) && meta.row_sums[r] > 0) {
        violations.push({
          rule_name: "line_all_negative_row",
          locations: [{ row: r, col: -1 }],
        });
      }
    }

    // Check column sums
    for (let c = 0; c < cols.value; c++) {
      const col_sum = weighted_sum_col(state, c, [KakurasuCell.BLACK]);

      if (col_sum > meta.col_sums[c]) {
        violations.push({
          rule_name: "line_sum_col_exceeded",
          locations: [{ row: -1, col: c }],
        });
      }

      if (all_cells_in_col(state, c, [KakurasuCell.CROSS]) && meta.col_sums[c] > 0) {
        violations.push({
          rule_name: "line_all_negative_col",
          locations: [{ row: -1, col: c }],
        });
      }
    }

    return violations;
  }

  /**
   * Toggle all cells in a row/column between two states
   * Used for gutter clicking functionality
   *
   * Logic:
   * - If any editable cell is empty → set all empty cells to to_state
   * - If no editable cells are empty → set all to_state cells back to from_state
   * - Cells with other values (e.g. BLACK) are ignored
   */
  function handle_line_toggle(
    is_row: boolean,
    index: number,
    from_state: number,
    to_state: number
  ): { changes: Array<{ row: number; col: number; old_value: number; new_value: number }> } {
    const changes: Array<{ row: number; col: number; old_value: number; new_value: number }> = [];
    const length = is_row ? cols.value : rows.value;

    // Collect editable cells in this line
    const cells: Array<{ row: number; col: number; value: number }> = [];
    for (let i = 0; i < length; i++) {
      const row = is_row ? index : i;
      const col = is_row ? i : index;
      if (!is_cell_editable(row, col)) continue;
      cells.push({ row, col, value: get_cell(row, col) });
    }

    // Check if any cell is empty
    const has_empty = cells.some((c) => c.value === from_state);

    if (has_empty) {
      // Set all empty cells to to_state
      for (const { row, col, value } of cells) {
        if (value === from_state) {
          set_cell(row, col, to_state);
          changes.push({ row, col, old_value: value, new_value: to_state });
        }
      }
    } else {
      // No empty cells - set all to_state cells back to from_state
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
    immutable_cells,
    handle_cell_click,
    set_cell_value,
    check_solution: () => solution_checker.check(board.value),
    clear,
    get_violations,
    handle_line_toggle,
    definition,
  };
}
