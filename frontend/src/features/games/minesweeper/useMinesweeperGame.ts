/**
 * useMinesweeperGame - Core game logic for Minesweeper
 *
 * Mode-agnostic: works in both freeplay and experiment contexts.
 * Uses the new game primitives architecture.
 */
import { computed, type ComputedRef, type Ref } from "vue";
import { useBoardState } from "@/core/games/composables";
import { useStateCycler } from "@/core/games/composables";
import { useSolutionChecker } from "@/core/games/composables";
import type { Cell, RuleViolation } from "@/core/games/types/puzzle-types";
import type { PuzzleDefinition } from "@/core/games/types/puzzle-types.ts";

/**
 * Minesweeper cell values (research format)
 */
export const MinesweeperCell = {
  UNMARKED: -1,
  ONE: 1,
  TWO: 2,
  THREE: 3,
  FOUR: 4,
  FIVE: 5,
  SIX: 6,
  SEVEN: 7,
  EIGHT: 8,
  FLAG: -3,
  SAFE: -4,
  EMPTY: 0,
} as const;

export type MinesweeperCellValue = (typeof MinesweeperCell)[keyof typeof MinesweeperCell];

export interface MinesweeperGameReturn {
  /** Current board state */
  board: Ref<number[][]>;

  /** Initial state for reference */
  initial_state: Readonly<number[][]>;

  /** Number of rows */
  rows: ComputedRef<number>;

  /** Number of columns */
  cols: ComputedRef<number>;

  /** Immutable cells matrix */
  immutable_cells: ComputedRef<number[][]>;

  /** Handle cell click - returns old/new values for recording */
  handle_cell_click: (
    row: number,
    col: number,
    button: number
  ) => { old_value: number; new_value: number } | null;

  /** Set cell to specific value (for drag operations) - returns old/new values for recording */
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

  /** Count of unmarked cells */
  unmarked_count: ComputedRef<number>;

  /** Puzzle definition */
  definition: PuzzleDefinition;
}

/**
 * Create Minesweeper game logic
 */
export function useMinesweeperGame(
  definition: PuzzleDefinition,
  saved_board?: number[][] | null
): MinesweeperGameReturn {
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
    is_editable: (initial_value) => initial_value === MinesweeperCell.UNMARKED,
  });

  // State cycler for click behavior
  const { cycle_state } = useStateCycler([
    MinesweeperCell.UNMARKED,
    MinesweeperCell.FLAG,
    MinesweeperCell.SAFE,
  ]);

  // Solution checker
  const solution_checker = useSolutionChecker({
    type: "cell-grid",
    solution_hash: definition.solution_hash,
    positive_values: [MinesweeperCell.FLAG],
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
      return null; // No change needed
    }

    set_cell(row, col, value);
    return { old_value, new_value: value };
  }

  /**
   * Get rule violations (too many flags around a number)
   */
  function get_violations(): RuleViolation[] {
    const violations: RuleViolation[] = [];
    const state = board.value;

    // All 8 directions
    const directions = [
      [-1, -1], [-1, 0], [-1, 1],
      [0, -1],          [0, 1],
      [1, -1], [1, 0], [1, 1],
    ];

    const violating_cells: Cell[] = [];

    for (let r = 0; r < rows.value; r++) {
      for (let c = 0; c < cols.value; c++) {
        const cell_value = state[r][c];

        // Skip if not a numbered cell (1-8)
        if (cell_value < 1 || cell_value > 8) continue;

        // Count surrounding flags
        let flag_count = 0;
        for (const [dr, dc] of directions) {
          const nr = r + dr;
          const nc = c + dc;
          if (nr >= 0 && nr < rows.value && nc >= 0 && nc < cols.value) {
            if (state[nr][nc] === MinesweeperCell.FLAG) {
              flag_count++;
            }
          }
        }

        // Too many flags
        if (flag_count > cell_value) {
          violating_cells.push({ row: r, col: c });
        }
      }
    }

    if (violating_cells.length > 0) {
      violations.push({
        rule_name: "minesweeper_surrounding_flag_violation",
        locations: violating_cells,
      });
    }

    return violations;
  }

  // Computed: count of unmarked cells
  const unmarked_count = computed(() =>
    board.value.flat().filter((c) => c === MinesweeperCell.UNMARKED).length
  );

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
    unmarked_count,
    definition,
  };
}
