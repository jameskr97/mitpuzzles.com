/**
 * useMosaicGame - Core game logic for Mosaic
 *
 * Mode-agnostic: works in both freeplay and experiment contexts.
 */
import { computed, type ComputedRef, type Ref } from "vue";
import { useBoardState } from "@/core/games/composables";
import { useStateCycler } from "@/core/games/composables";
import { useSolutionChecker } from "@/core/games/composables";
import type { PuzzleDefinition, RuleViolation } from "@/core/games/types/puzzle-types.ts";

/**
 * Mosaic cell values (research format)
 * Numbers 0-9 are clues, -1 is unmarked, -3 is shaded, -4 is cross
 */
export const MosaicCell = {
  ZERO: 0,
  ONE: 1,
  TWO: 2,
  THREE: 3,
  FOUR: 4,
  FIVE: 5,
  SIX: 6,
  SEVEN: 7,
  EIGHT: 8,
  NINE: 9,
  UNMARKED: -1,
  SHADED: -3,
  CROSS: -4,
} as const;

export type MosaicCellValue = (typeof MosaicCell)[keyof typeof MosaicCell];

/**
 * Convert board for play - numbered cells become UNMARKED
 */
function convert_board_for_play(board: number[][]): number[][] {
  return board.map((row) =>
    row.map((cell) => (cell >= MosaicCell.ZERO && cell <= MosaicCell.NINE ? MosaicCell.UNMARKED : cell))
  );
}

export interface MosaicGameReturn {
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
  /** Get number clue at position (from initial_state) */
  get_number_clue: (row: number, col: number) => number | null;
  definition: PuzzleDefinition;
}

/**
 * Create Mosaic game logic
 */
export function useMosaicGame(
  definition: PuzzleDefinition,
  saved_board?: number[][] | null
): MosaicGameReturn {
  // For play, numbered cells become UNMARKED (but we keep initial_state for reference)
  // Uses research format directly (no conversion needed)
  const play_initial = convert_board_for_play(definition.initial_state);

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
  } = useBoardState(play_initial, saved_board ?? null, {
    is_editable: () => true, // All cells editable in Mosaic
  });

  const { cycle_state } = useStateCycler([
    MosaicCell.UNMARKED,
    MosaicCell.SHADED,
    MosaicCell.CROSS,
  ]);

  const solution_checker = useSolutionChecker({
    type: "cell-grid",
    solution_hash: definition.solution_hash,
    positive_values: [MosaicCell.SHADED],
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

  function get_number_clue(row: number, col: number): number | null {
    const value = definition.initial_state[row]?.[col];
    if (value !== undefined && value >= MosaicCell.ZERO && value <= MosaicCell.NINE) {
      return value;
    }
    return null;
  }

  function get_violations(): RuleViolation[] {
    const violations: RuleViolation[] = [];
    const state = board.value;

    for (let r = 0; r < rows.value; r++) {
      for (let c = 0; c < cols.value; c++) {
        const clue = get_number_clue(r, c);
        if (clue === null) continue;

        // Count shaded cells in 3x3 region
        let shaded_count = 0;
        for (let dr = -1; dr <= 1; dr++) {
          for (let dc = -1; dc <= 1; dc++) {
            const nr = r + dr, nc = c + dc;
            if (nr >= 0 && nr < rows.value && nc >= 0 && nc < cols.value) {
              if (state[nr][nc] === MosaicCell.SHADED) {
                shaded_count++;
              }
            }
          }
        }

        if (shaded_count > clue) {
          violations.push({
            rule_name: "mosaic_shaded_count_violation",
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
    immutable_cells,
    handle_cell_click,
    set_cell_value,
    check_solution: () => solution_checker.check(board.value),
    clear,
    get_violations,
    get_number_clue,
    definition,
  };
}
