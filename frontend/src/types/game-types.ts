/**
 * Common type definitions for the game engine primitives
 */

/**
 * Cell position in the grid
 */
export interface Cell {
  row: number;
  col: number;
}

/**
 * Rule violation reported by constraint checkers
 */
export interface RuleViolation {
  rule_name: string;
  locations: Cell[];
}

/**
 * Rule definition for constraint checking
 */
export interface RuleDefinition {
  name: string;
  check: (board: number[][], context?: any) => RuleViolation | null;
}

/**
 * Puzzle definition from backend
 */
export interface PuzzleDefinition<TMeta = any> {
  id: string;
  puzzle_type: string;
  rows: number;
  cols: number;
  size?: string;
  difficulty?: string;
  initial_state: number[][];
  solution?: number[][];
  solution_hash?: string;
  meta?: TMeta;
}

/**
 * Solution checker configuration
 */
export interface SolutionCheckerConfig {
  type: "cell-grid" | "connection" | "custom";
  solution_hash?: string;
  expected_solution?: number[][] | any;
  /**
   * For cell-grid type: which cell values count as "positive" (marked/filled)
   * Used for run-length encoding
   */
  positive_values?: number[];
  /**
   * Custom encoder function for non-standard games
   */
  custom_encoder?: (state: any) => string;
}

/**
 * Data recorder configuration
 */
export interface DataRecorderConfig {
  mode: "freeplay" | "experiment";
  puzzle_type: string;
  // Freeplay-specific
  persist?: boolean;
  broadcast?: boolean;
  // Experiment-specific
  executor?: any; // GraphExecutor type
  trial_id?: string;
  node_id?: string;
}

/**
 * Recorded interaction event
 */
export interface RecordedInteraction {
  type: "cell_click" | "cell_keypress" | "cell_focus" | "clear" | "attempt_solve";
  timestamp: number;
  data: Record<string, any>;
}

/**
 * Connection for Hashi-like games
 */
export interface Connection<T = any> {
  from: Cell;
  to: Cell;
  data?: T;
}

/**
 * Drag interaction configuration
 */
export interface DragInteractionConfig<TConnection = any> {
  /**
   * Find valid drag targets from a starting cell
   */
  find_valid_targets: (from: Cell, board: number[][]) => Cell[];

  /**
   * Check if a connection would be valid (e.g., doesn't cross existing connections)
   */
  is_valid_connection: (from: Cell, to: Cell, existing: TConnection[]) => boolean;

  /**
   * Create or toggle a connection between two cells
   */
  toggle_connection: (
    from: Cell,
    to: Cell,
    button: number,
    existing: TConnection[]
  ) => TConnection[];
}
