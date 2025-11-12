/**
 * useMinesweeperGame - Core game logic for Minesweeper
 *
 * Mode-agnostic: works in both freeplay and experiment contexts.
 * Uses the new game primitives architecture.
 */
import { computed, type ComputedRef, type Ref } from "vue";
import { useBoardState } from "@/composables/game-primitives";
import { useStateCycler } from "@/composables/game-primitives";
import { useSolutionChecker } from "@/composables/game-primitives";
import type { Cell, RuleViolation } from "@/types/game-types";
import type { PuzzleDefinition } from "@/services/game/engines/types";

/**
 * Minesweeper cell values
 * Defined locally - no dependency on translator.ts
 */
export const MinesweeperCell = {
  UNMARKED: 0,
  ONE: 1,
  TWO: 2,
  THREE: 3,
  FOUR: 4,
  FIVE: 5,
  SIX: 6,
  SEVEN: 7,
  EIGHT: 8,
  FLAG: 9,
  SAFE: 10,
  EMPTY: 11,
  QUESTION_MARK: 12,
  UNMARKED_HIGHLIGHTED: 13,
} as const;

export type MinesweeperCellValue = (typeof MinesweeperCell)[keyof typeof MinesweeperCell];

/**
 * Research format to game format mapping
 */
const RESEARCH_TO_GAME: Record<number, number> = {
  0: MinesweeperCell.EMPTY,
  1: MinesweeperCell.ONE,
  2: MinesweeperCell.TWO,
  3: MinesweeperCell.THREE,
  4: MinesweeperCell.FOUR,
  5: MinesweeperCell.FIVE,
  6: MinesweeperCell.SIX,
  7: MinesweeperCell.SEVEN,
  8: MinesweeperCell.EIGHT,
  [-1]: MinesweeperCell.UNMARKED,
  [-3]: MinesweeperCell.FLAG,
  [-4]: MinesweeperCell.SAFE,
};

/**
 * Convert research format board to game format
 */
export function convert_research_board(research_board: number[][]): number[][] {
  return research_board.map((row) =>
    row.map((cell) => RESEARCH_TO_GAME[cell] ?? cell)
  );
}

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
  // Convert initial state from research format
  const converted_initial = convert_research_board(definition.initial_state);
  const converted_saved = saved_board ? saved_board : null;

  // Board state management
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
