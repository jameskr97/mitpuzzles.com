/**
 * useLightupGame - Core game logic for Lightup (Akari)
 *
 * Mode-agnostic: works in both freeplay and experiment contexts.
 * Uses the new game primitives architecture.
 */
import { computed, type ComputedRef, type Ref } from "vue";
import { useBoardState } from "@/composables/game-primitives";
import { useStateCycler } from "@/composables/game-primitives";
import { useSolutionChecker } from "@/composables/game-primitives";
import type { RuleViolation } from "@/types/game-types";
import type { PuzzleDefinition } from "@/services/game/engines/types";

/**
 * Lightup cell values
 */
export const LightupCell = {
  WALL_0: 0,
  WALL_1: 1,
  WALL_2: 2,
  WALL_3: 3,
  WALL_4: 4,
  WALL_NO_CONSTRAINT: 5,
  EMPTY: 6,
  BULB: 7,
  CROSS: 8,
} as const;

export type LightupCellValue = (typeof LightupCell)[keyof typeof LightupCell];

/** Wall states for checking */
export const WALL_STATES = [
  LightupCell.WALL_0,
  LightupCell.WALL_1,
  LightupCell.WALL_2,
  LightupCell.WALL_3,
  LightupCell.WALL_4,
  LightupCell.WALL_NO_CONSTRAINT,
];

/** Numbered wall states */
export const NUMBERED_WALLS = [
  LightupCell.WALL_0,
  LightupCell.WALL_1,
  LightupCell.WALL_2,
  LightupCell.WALL_3,
  LightupCell.WALL_4,
];

/** Cardinal directions for light propagation */
const DIRECTIONS = [
  [-1, 0], // up
  [1, 0],  // down
  [0, -1], // left
  [0, 1],  // right
];

/**
 * Compute which cells are lit by bulbs on a board
 * @param board - 2D array of cell values
 * @param rows - number of rows
 * @param cols - number of columns
 * @returns flat array of booleans indicating which cells are lit
 */
export function compute_lit_cells(board: number[][], rows: number, cols: number): boolean[] {
  const lit = new Array(rows * cols).fill(false);

  for (let row = 0; row < rows; row++) {
    for (let col = 0; col < cols; col++) {
      if (board[row][col] !== LightupCell.BULB) continue;

      // Propagate light in each cardinal direction
      for (const [dy, dx] of DIRECTIONS) {
        let nr = row + dy;
        let nc = col + dx;

        while (nr >= 0 && nr < rows && nc >= 0 && nc < cols) {
          if (WALL_STATES.includes(board[nr][nc])) break;
          lit[nr * cols + nc] = true;
          nr += dy;
          nc += dx;
        }
      }
    }
  }

  return lit;
}

/**
 * Research format to game format mapping
 */
const RESEARCH_TO_GAME: Record<number, number> = {
  [0]: LightupCell.WALL_0,
  [1]: LightupCell.WALL_1,
  [2]: LightupCell.WALL_2,
  [3]: LightupCell.WALL_3,
  [4]: LightupCell.WALL_4,
  [-2]: LightupCell.WALL_NO_CONSTRAINT,
  [-1]: LightupCell.EMPTY,
  [-3]: LightupCell.BULB,
  [-4]: LightupCell.CROSS,
};

/**
 * Convert research format board to game format
 */
export function convert_research_board(research_board: number[][]): number[][] {
  return research_board.map((row) =>
    row.map((cell) => RESEARCH_TO_GAME[cell] ?? cell)
  );
}

export interface LightupGameReturn {
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

  /** Set cell to specific value (for drag operations) */
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

  /** Get lit cells (computed) */
  lit_cells: ComputedRef<boolean[]>;

  /** Puzzle definition */
  definition: PuzzleDefinition;
}

/**
 * Create Lightup game logic
 */
export function useLightupGame(
  definition: PuzzleDefinition,
  saved_board?: number[][] | null
): LightupGameReturn {
  // Convert initial state from research format
  const converted_initial = convert_research_board(definition.initial_state);
  const converted_saved = saved_board ? saved_board : null;

  // Board state management - only EMPTY cells are editable
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
    is_editable: (initial_value) => initial_value === LightupCell.EMPTY,
  });

  // State cycler for click behavior
  const { cycle_state } = useStateCycler([
    LightupCell.EMPTY,
    LightupCell.BULB,
    LightupCell.CROSS,
  ]);

  // Solution checker
  const solution_checker = useSolutionChecker({
    type: "cell-grid",
    solution_hash: definition.solution_hash,
    positive_values: [LightupCell.BULB],
  });

  // Cardinal directions
  const DIRECTIONS = [
    [-1, 0], // up
    [1, 0],  // down
    [0, -1], // left
    [0, 1],  // right
  ];

  /**
   * Calculate which cells are lit by bulbs
   */
  const lit_cells = computed(() => {
    const r = rows.value;
    const c = cols.value;
    const state = board.value;
    const lit = new Array(r * c).fill(false);

    // For each bulb, propagate light in all 4 directions
    for (let row = 0; row < r; row++) {
      for (let col = 0; col < c; col++) {
        if (state[row][col] !== LightupCell.BULB) continue;

        // Propagate light in each cardinal direction
        for (const [dy, dx] of DIRECTIONS) {
          let nr = row + dy;
          let nc = col + dx;

          // Continue until hitting a wall or boundary
          while (nr >= 0 && nr < r && nc >= 0 && nc < c) {
            const i = nr * c + nc;

            // Stop if we hit a wall
            if (WALL_STATES.includes(state[nr][nc])) {
              break;
            }

            lit[i] = true;
            nr += dy;
            nc += dx;
          }
        }
      }
    }

    return lit;
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
      return null;
    }

    set_cell(row, col, value);
    return { old_value, new_value: value };
  }

  /**
   * Helper to check if position is in bounds
   */
  function in_bounds(r: number, c: number): boolean {
    return r >= 0 && r < rows.value && c >= 0 && c < cols.value;
  }

  /**
   * Get rule violations
   */
  function get_violations(): RuleViolation[] {
    const violations: RuleViolation[] = [];
    const state = board.value;

    // 1. Check for bulbs lighting each other
    const bulbs: [number, number][] = [];
    for (let r = 0; r < rows.value; r++) {
      for (let c = 0; c < cols.value; c++) {
        if (state[r][c] === LightupCell.BULB) {
          bulbs.push([r, c]);
        }
      }
    }

    const hit = new Set<string>();
    for (const [r, c] of bulbs) {
      for (const [dr, dc] of DIRECTIONS) {
        let nr = r + dr;
        let nc = c + dc;

        while (in_bounds(nr, nc) && !WALL_STATES.includes(state[nr][nc])) {
          if (state[nr][nc] === LightupCell.BULB) {
            hit.add(`${r},${c}`);
            hit.add(`${nr},${nc}`);
            break;
          }
          nr += dr;
          nc += dc;
        }
      }
    }

    if (hit.size > 0) {
      const locations = Array.from(hit).map((key) => {
        const [row, col] = key.split(",").map(Number);
        return { row, col };
      });
      violations.push({
        rule_name: "bulb_intersection_violation",
        locations,
      });
    }

    // 2. Check numbered wall constraints
    const wall_violations: { row: number; col: number }[] = [];
    for (let r = 0; r < rows.value; r++) {
      for (let c = 0; c < cols.value; c++) {
        const cell = state[r][c];
        if (!NUMBERED_WALLS.includes(cell)) continue;

        const required = cell; // Wall value is the required count

        let bulb_count = 0;
        for (const [dr, dc] of DIRECTIONS) {
          const nr = r + dr;
          const nc = c + dc;
          if (in_bounds(nr, nc) && state[nr][nc] === LightupCell.BULB) {
            bulb_count++;
          }
        }

        if (bulb_count > required) {
          wall_violations.push({ row: r, col: c });
        }
      }
    }

    if (wall_violations.length > 0) {
      violations.push({
        rule_name: "numbered_wall_constraint_violated",
        locations: wall_violations,
      });
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
    lit_cells,
    definition,
  };
}
