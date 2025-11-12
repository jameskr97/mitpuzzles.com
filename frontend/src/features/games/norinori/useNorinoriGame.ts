/**
 * useNorinoriGame - Core game logic for Norinori
 *
 * Mode-agnostic: works in both freeplay and experiment contexts.
 *
 * Rules:
 * - Each region must contain exactly 2 shaded cells
 * - Every shaded cell must be adjacent to exactly one other shaded cell (forming dominoes)
 * - Dominoes can span across region boundaries
 */
import { computed, type ComputedRef, type Ref } from "vue";
import {
  useBoardState,
  useStateCycler,
  useSolutionChecker,
  count_adjacent,
  get_region_cells,
  get_all_region_ids,
  get_region_at,
  same_region as same_region_util,
  ORTHOGONAL_DIRECTIONS,
} from "@/composables/game-primitives";
import type { RuleViolation } from "@/types/game-types";
import type { PuzzleDefinition } from "@/services/game/engines/types";

/**
 * Norinori cell values
 */
export const NorinoriCell = {
  EMPTY: -1,
  SHADED: -3,
  CROSS: -4,
} as const;

export type NorinoriCellValue = (typeof NorinoriCell)[keyof typeof NorinoriCell];

export interface NorinoriMeta {
  regions: number[][];
}

export interface NorinoriGameReturn {
  board: Ref<number[][]>;
  initial_state: Readonly<number[][]>;
  rows: ComputedRef<number>;
  cols: ComputedRef<number>;
  region_map: number[][];
  handle_cell_click: (row: number, col: number, button: number) => { old_value: number; new_value: number } | null;
  set_cell_value: (row: number, col: number, value: number) => { old_value: number; new_value: number } | null;
  check_solution: () => Promise<boolean>;
  clear: () => void;
  get_violations: () => RuleViolation[];
  /** Get region ID for a cell */
  get_region: (row: number, col: number) => number;
  /** Check if two adjacent cells are in the same region */
  same_region: (r1: number, c1: number, r2: number, c2: number) => boolean;
  definition: PuzzleDefinition<NorinoriMeta>;
}

/**
 * Create Norinori game logic
 */
export function useNorinoriGame(
  definition: PuzzleDefinition<NorinoriMeta>,
  saved_board?: number[][] | null
): NorinoriGameReturn {
  const region_map = definition.meta?.regions || [];

  // Initialize board with EMPTY cells
  const initial_board = definition.initial_state.map((row) =>
    row.map(() => NorinoriCell.EMPTY)
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
    NorinoriCell.EMPTY,
    NorinoriCell.SHADED,
    NorinoriCell.CROSS,
  ]);

  const solution_checker = useSolutionChecker({
    type: "cell-grid",
    solution_hash: definition.solution_hash,
    positive_values: [NorinoriCell.SHADED],
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

  function get_violations(): RuleViolation[] {
    const violations: RuleViolation[] = [];
    const state = board.value;

    // Check each shaded cell forms part of a valid domino (exactly 1 adjacent shaded)
    for (let r = 0; r < rows.value; r++) {
      for (let c = 0; c < cols.value; c++) {
        if (state[r][c] === NorinoriCell.SHADED) {
          const adjacent = count_adjacent(state, r, c, [NorinoriCell.SHADED], ORTHOGONAL_DIRECTIONS);
          if (adjacent !== 1) {
            violations.push({
              rule_name: "norinori_domino_violation",
              locations: [{ row: r, col: c }],
            });
          }
        }
      }
    }

    // Check each region has exactly 2 shaded cells
    const regions = get_all_region_ids(region_map);
    for (const region_id of regions) {
      const cells = get_region_cells(region_map, region_id);
      const shaded_cells = cells.filter(([r, c]) => state[r][c] === NorinoriCell.SHADED);

      if (shaded_cells.length > 2) {
        // Too many shaded cells in region
        for (const [r, c] of shaded_cells) {
          violations.push({
            rule_name: "norinori_region_count_violation",
            locations: [{ row: r, col: c }],
          });
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
    region_map,
    handle_cell_click,
    set_cell_value,
    check_solution: () => solution_checker.check(board.value),
    clear,
    get_violations,
    get_region,
    same_region,
    definition,
  };
}
