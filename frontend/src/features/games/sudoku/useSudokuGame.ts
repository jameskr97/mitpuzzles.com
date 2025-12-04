/**
 * useSudokuGame - Core game logic for Sudoku
 *
 * Mode-agnostic: works in both freeplay and experiment contexts.
 */
import { computed, type ComputedRef, type Ref } from "vue";
import { useBoardState } from "@/core/games/composables";
import { useSolutionChecker } from "@/core/games/composables";
import type { PuzzleDefinition, RuleViolation } from "@/core/games/types/puzzle-types.ts";

/**
 * Sudoku cell values (research format)
 * -1 is empty, 1-9 are numbers
 */
export const SudokuCell = {
  EMPTY: -1,
} as const;

export interface SudokuGameReturn {
  board: Ref<number[][]>;
  initial_state: Readonly<number[][]>;
  rows: ComputedRef<number>;
  cols: ComputedRef<number>;
  immutable_cells: ComputedRef<number[][]>;
  /** Handle keyboard input for a cell */
  handle_key_input: (row: number, col: number, key: string) => { old_value: number; new_value: number } | null;
  /** Set cell to specific value */
  set_cell_value: (row: number, col: number, value: number) => { old_value: number; new_value: number } | null;
  check_solution: () => Promise<boolean>;
  clear: () => void;
  get_violations: () => RuleViolation[];
  /** Check if a cell is prefilled */
  is_prefilled: (row: number, col: number) => boolean;
  /** Box size (sqrt of grid size) */
  box_size: ComputedRef<number>;
  definition: PuzzleDefinition;
}

/**
 * Create Sudoku game logic
 */
export function useSudokuGame(
  definition: PuzzleDefinition,
  saved_board?: number[][] | null
): SudokuGameReturn {
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
    is_editable: (initial_value) => initial_value === SudokuCell.EMPTY,
  });

  const solution_checker = useSolutionChecker({
    type: "cell-grid",
    solution_hash: definition.solution_hash,
    positive_values: [1, 2, 3, 4, 5, 6, 7, 8, 9],
  });

  const box_size = computed(() => Math.sqrt(rows.value));

  function handle_key_input(row: number, col: number, key: string) {
    if (!is_cell_editable(row, col)) return null;

    const old_value = get_cell(row, col);
    let new_value: number;

    if (key === "Backspace" || key === "Delete" || key === "0") {
      new_value = SudokuCell.EMPTY;
    } else {
      const num = parseInt(key);
      if (isNaN(num) || num < 1 || num > rows.value) return null;
      new_value = num;
    }

    if (old_value === new_value) return null;
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

  function is_prefilled(row: number, col: number): boolean {
    return definition.initial_state[row][col] !== SudokuCell.EMPTY;
  }

  function get_violations(): RuleViolation[] {
    const violations: RuleViolation[] = [];
    const state = board.value;
    const r = rows.value;
    const c = cols.value;
    const bs = box_size.value;

    // Check rows
    for (let row = 0; row < r; row++) {
      const seen = new Map<number, number>();
      for (let col = 0; col < c; col++) {
        const value = state[row][col];
        if (value === SudokuCell.EMPTY) continue;
        if (seen.has(value)) {
          violations.push({
            rule_name: "row_duplicate_violation",
            locations: [
              { row, col: seen.get(value)! },
              { row, col },
            ],
          });
        } else {
          seen.set(value, col);
        }
      }
    }

    // Check columns
    for (let col = 0; col < c; col++) {
      const seen = new Map<number, number>();
      for (let row = 0; row < r; row++) {
        const value = state[row][col];
        if (value === SudokuCell.EMPTY) continue;
        if (seen.has(value)) {
          violations.push({
            rule_name: "col_duplicate_violation",
            locations: [
              { row: seen.get(value)!, col },
              { row, col },
            ],
          });
        } else {
          seen.set(value, row);
        }
      }
    }

    // Check boxes
    for (let br = 0; br < r; br += bs) {
      for (let bc = 0; bc < c; bc += bs) {
        const seen = new Map<number, { row: number; col: number }>();
        for (let row = br; row < br + bs; row++) {
          for (let col = bc; col < bc + bs; col++) {
            const value = state[row][col];
            if (value === SudokuCell.EMPTY) continue;
            if (seen.has(value)) {
              violations.push({
                rule_name: "box_duplicate_violation",
                locations: [seen.get(value)!, { row, col }],
              });
            } else {
              seen.set(value, { row, col });
            }
          }
        }
      }
    }

    return violations;
  }

  return {
    board,
    initial_state,
    rows,
    cols,
    immutable_cells,
    handle_key_input,
    set_cell_value,
    check_solution: () => solution_checker.check(board.value),
    clear,
    get_violations,
    is_prefilled,
    box_size,
    definition,
  };
}
