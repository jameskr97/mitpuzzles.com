/**
 * useNonogramsGame - Core game logic for Nonograms
 *
 * Mode-agnostic: works in both freeplay and experiment contexts.
 */
import { computed, type ComputedRef, type Ref } from "vue";
import { useBoardState } from "@/composables/game-primitives";
import { useStateCycler } from "@/composables/game-primitives";
import { useSolutionChecker } from "@/composables/game-primitives";
import type { RuleViolation } from "@/types/game-types";
import type { PuzzleDefinition, NonogramMeta } from "@/services/game/engines/types";

/**
 * Nonograms cell values
 */
export const NonogramsCell = {
  EMPTY: 0,
  BLACK: 1,
  CROSS: 2,
} as const;

export type NonogramsCellValue = (typeof NonogramsCell)[keyof typeof NonogramsCell];

/**
 * Research format to game format mapping
 */
const RESEARCH_TO_GAME: Record<number, number> = {
  [-1]: NonogramsCell.EMPTY,
  [0]: NonogramsCell.CROSS,
  [1]: NonogramsCell.BLACK,
};

/**
 * Convert research format board to game format
 */
export function convert_research_board(research_board: number[][]): number[][] {
  return research_board.map((row) =>
    row.map((cell) => RESEARCH_TO_GAME[cell] ?? cell)
  );
}

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
  const converted_initial = convert_research_board(definition.initial_state);
  const converted_saved = saved_board ? saved_board : null;

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
  } = useBoardState(converted_initial, converted_saved, {
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
