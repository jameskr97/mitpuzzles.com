/**
 * useTentsGame - Core game logic for Tents
 *
 * Mode-agnostic: works in both freeplay and experiment contexts.
 */
import { type ComputedRef, type Ref } from "vue";
import { useBoardState } from "@/core/games/composables";
import { useStateCycler } from "@/core/games/composables";
import { useSolutionChecker } from "@/core/games/composables";
import type { PuzzleDefinition, TentsMeta, RuleViolation } from "@/core/games/types/puzzle-types.ts";

/**
 * Tents cell values (research format)
 */
export const TentsCell = {
  EMPTY: -1,
  TREE: 1,
  TENT: -3,
  GREEN: -4,
} as const;

export type TentsCellValue = (typeof TentsCell)[keyof typeof TentsCell];

export interface TentsGameReturn {
  board: Ref<number[][]>;
  initial_state: Readonly<number[][]>;
  rows: ComputedRef<number>;
  cols: ComputedRef<number>;
  immutable_cells: ComputedRef<number[][]>;
  handle_cell_click: (row: number, col: number, button: number) => { old_value: number; new_value: number } | null;
  set_cell_value: (row: number, col: number, value: number) => { old_value: number; new_value: number } | null;
  check_solution: () => Promise<boolean>;
  clear: () => void;
  get_violations: () => RuleViolation[];
  handle_line_toggle: (
    is_row: boolean,
    index: number,
    from_state: number,
    to_state: number
  ) => { changes: Array<{ row: number; col: number; old_value: number; new_value: number }> };
  definition: PuzzleDefinition<TentsMeta>;
}

/**
 * Create Tents game logic
 */
export function useTentsGame(
  definition: PuzzleDefinition<TentsMeta>,
  saved_board?: number[][] | null
): TentsGameReturn {
  // Board state management
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
    is_editable: (initial_value) => initial_value !== TentsCell.TREE,
  });

  const { cycle_state } = useStateCycler([
    TentsCell.EMPTY,
    TentsCell.TENT,
    TentsCell.GREEN,
  ]);

  const solution_checker = useSolutionChecker({
    type: "cell-grid",
    solution_hash: definition.solution_hash,
    positive_values: [TentsCell.TENT],
  });

  const DIRECTIONS_8 = [
    [-1, -1], [-1, 0], [-1, 1],
    [0, -1],          [0, 1],
    [1, -1], [1, 0], [1, 1],
  ];

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

  function in_bounds(r: number, c: number): boolean {
    return r >= 0 && r < rows.value && c >= 0 && c < cols.value;
  }

  function get_violations(): RuleViolation[] {
    const violations: RuleViolation[] = [];
    const state = board.value;
    const meta = definition.meta!;

    // 1. Check for adjacent tents
    const tent_violations: { row: number; col: number }[] = [];
    for (let r = 0; r < rows.value; r++) {
      for (let c = 0; c < cols.value; c++) {
        if (state[r][c] !== TentsCell.TENT) continue;
        for (const [dr, dc] of DIRECTIONS_8) {
          const nr = r + dr, nc = c + dc;
          if (in_bounds(nr, nc) && state[nr][nc] === TentsCell.TENT) {
            tent_violations.push({ row: r, col: c });
            break;
          }
        }
      }
    }
    if (tent_violations.length > 0) {
      violations.push({ rule_name: "tents_intersecting", locations: tent_violations });
    }

    // 2. Check row tent counts exceeded
    for (let r = 0; r < rows.value; r++) {
      const tent_count = state[r].filter((v) => v === TentsCell.TENT).length;
      if (tent_count > meta.row_tent_counts[r]) {
        violations.push({ rule_name: "line_sum_row_exceeded", locations: [{ row: r, col: -1 }] });
      }
    }

    // 3. Check column tent counts exceeded
    for (let c = 0; c < cols.value; c++) {
      let tent_count = 0;
      for (let r = 0; r < rows.value; r++) {
        if (state[r][c] === TentsCell.TENT) tent_count++;
      }
      if (tent_count > meta.col_tent_counts[c]) {
        violations.push({ rule_name: "line_sum_col_exceeded", locations: [{ row: -1, col: c }] });
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
   * - Cells with other values (e.g. tents, trees) are ignored
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
