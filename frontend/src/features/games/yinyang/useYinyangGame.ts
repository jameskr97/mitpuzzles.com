/**
 * useYinyangGame - core game logic for yin-yang
 *
 * mode-agnostic: works in both freeplay and experiment contexts.
 *
 * rules:
 * - fill every cell black or white
 * - all black cells must be orthogonally connected
 * - all white cells must be orthogonally connected
 * - no 2x2 region may be entirely one color
 *
 * cell encoding:
 *   initial_state: 1 = black clue, 2 = white clue, -1 = empty
 *   board (play): -3 = black, -4 = white, -1 = empty
 */
import { type ComputedRef, type Ref } from "vue";
import { useBoardState } from "@/core/games/composables";
import { useStateCycler } from "@/core/games/composables";
import { useSolutionChecker } from "@/core/games/composables";
import type { PuzzleDefinition, RuleViolation } from "@/core/games/types/puzzle-types.ts";

export const YinyangCell = {
  EMPTY: -1,
  BLACK: -3,
  WHITE: -4,
  CLUE_BLACK: 1,
  CLUE_WHITE: 2,
} as const;

export type YinyangCellValue = (typeof YinyangCell)[keyof typeof YinyangCell];

/**
 * convert clue cells to their play equivalents so the board is uniform
 */
function convert_board_for_play(board: number[][]): number[][] {
  return board.map((row) =>
    row.map((cell) => {
      if (cell === YinyangCell.CLUE_BLACK) return YinyangCell.BLACK;
      if (cell === YinyangCell.CLUE_WHITE) return YinyangCell.WHITE;
      return YinyangCell.EMPTY;
    })
  );
}

function is_clue(initial_state: number[][], row: number, col: number): boolean {
  const val = initial_state[row]?.[col];
  return val === YinyangCell.CLUE_BLACK || val === YinyangCell.CLUE_WHITE;
}

export interface YinyangGameReturn {
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
  definition: PuzzleDefinition;
}

export function useYinyangGame(
  definition: PuzzleDefinition,
  saved_board?: number[][] | null
): YinyangGameReturn {
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
    is_editable: (val) => val === YinyangCell.EMPTY,
  });

  const { cycle_state } = useStateCycler([
    YinyangCell.EMPTY,
    YinyangCell.BLACK,
    YinyangCell.WHITE,
  ]);

  const solution_checker = useSolutionChecker({
    type: "cell-grid",
    solution_hash: definition.solution_hash,
    positive_values: [YinyangCell.BLACK],
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
    const violations: RuleViolation[] = [];
    const state = board.value;
    const r = rows.value;
    const c = cols.value;

    // check no 2x2 monochrome blocks
    for (let row = 0; row < r - 1; row++) {
      for (let col = 0; col < c - 1; col++) {
        const tl = state[row][col];
        const tr = state[row][col + 1];
        const bl = state[row + 1][col];
        const br = state[row + 1][col + 1];

        if (tl === YinyangCell.EMPTY || tr === YinyangCell.EMPTY ||
            bl === YinyangCell.EMPTY || br === YinyangCell.EMPTY) continue;

        if (tl === tr && tr === bl && bl === br) {
          violations.push({
            rule_name: "yinyang_2x2_violation",
            locations: [
              { row, col }, { row, col: col + 1 },
              { row: row + 1, col }, { row: row + 1, col: col + 1 },
            ],
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
    definition,
  };
}
