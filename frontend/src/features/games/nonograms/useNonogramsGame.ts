/**
 * useNonogramsGame - Core game logic for Nonograms
 *
 * Mode-agnostic: works in both freeplay and experiment contexts.
 */
import { type ComputedRef, type Ref } from "vue";
import { useBoardState } from "@/core/games/composables";
import { useStateCycler } from "@/core/games/composables";
import { useSolutionChecker } from "@/core/games/composables";
import type { PuzzleDefinition, NonogramMeta, RuleViolation } from "@/core/games/types/puzzle-types.ts";

/**
 * Nonograms cell values (research format)
 */
export const NonogramsCell = {
  EMPTY: -1,
  BLACK: 1,
  CROSS: 0,
} as const;

export type NonogramsCellValue = (typeof NonogramsCell)[keyof typeof NonogramsCell];

export interface NonogramsGameReturn {
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
  definition: PuzzleDefinition<NonogramMeta>;
}

/**
 * Create Nonograms game logic
 */
export function useNonogramsGame(
  definition: PuzzleDefinition<NonogramMeta>,
  saved_board?: number[][] | null
): NonogramsGameReturn {
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
    is_editable: () => true, // All cells editable
  });

  const { cycle_state } = useStateCycler([
    NonogramsCell.EMPTY,
    NonogramsCell.BLACK,
    NonogramsCell.CROSS,
  ]);

  const solution_checker = useSolutionChecker({
    type: "cell-grid",
    solution_hash: definition.solution_hash,
    positive_values: [NonogramsCell.BLACK],
  });

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

  function get_violations(): RuleViolation[] {
    // Nonograms doesn't have tutorial violations in the original implementation
    return [];
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
    definition,
  };
}
