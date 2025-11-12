/**
 * useMosaicGame - Core game logic for Mosaic
 *
 * Mode-agnostic: works in both freeplay and experiment contexts.
 */
import { computed, type ComputedRef, type Ref } from "vue";
import { useBoardState } from "@/composables/game-primitives";
import { useStateCycler } from "@/composables/game-primitives";
import { useSolutionChecker } from "@/composables/game-primitives";
import type { RuleViolation } from "@/types/game-types";
import type { PuzzleDefinition } from "@/services/game/engines/types";

/**
 * Mosaic cell values
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
  UNMARKED: 10,
  SHADED: 11,
  CROSS: 12,
} as const;

export type MosaicCellValue = (typeof MosaicCell)[keyof typeof MosaicCell];

/**
 * Research format to game format mapping
 */
const RESEARCH_TO_GAME: Record<number, number> = {
  [0]: MosaicCell.ZERO,
  [1]: MosaicCell.ONE,
  [2]: MosaicCell.TWO,
  [3]: MosaicCell.THREE,
  [4]: MosaicCell.FOUR,
  [5]: MosaicCell.FIVE,
  [6]: MosaicCell.SIX,
  [7]: MosaicCell.SEVEN,
  [8]: MosaicCell.EIGHT,
  [9]: MosaicCell.NINE,
  [-1]: MosaicCell.UNMARKED,
  [-3]: MosaicCell.SHADED,
  [-4]: MosaicCell.CROSS,
};

/**
 * Convert research format board to game format
 */
export function convert_research_board(research_board: number[][]): number[][] {
  return research_board.map((row) =>
    row.map((cell) => RESEARCH_TO_GAME[cell] ?? cell)
  );
}

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
  const converted_initial = convert_research_board(definition.initial_state);
  // For play, numbered cells become UNMARKED (but we keep initial_state for reference)
  const play_initial = convert_board_for_play(converted_initial);
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
  } = useBoardState(play_initial, converted_saved, {
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
    const value = converted_initial[row]?.[col];
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
