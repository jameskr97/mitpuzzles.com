/**
 * useSolutionChecker - Solution validation for puzzles
 *
 * Supports multiple validation strategies:
 * - cell-grid: Run-length encoding for cell-state games
 * - connection: Bridge/edge-based encoding for Hashi-like games
 * - custom: User-provided encoder function
 */


export interface SolutionCheckerConfig {
  /**
   * Validation strategy type
   */
  type: "cell-grid" | "connection" | "custom";

  /**
   * Expected solution hash (from backend)
   */
  solution_hash?: string;

  /**
   * Expected solution board (alternative to hash)
   */
  expected_solution?: number[][];

  /**
   * For cell-grid: which cell values count as "positive" (marked/filled)
   */
  positive_values?: number[];

  /**
   * Custom encoder function for non-standard games
   */
  custom_encoder?: (state: any) => Promise<string> | string;
}

export interface SolutionCheckerReturn {
  /**
   * Check if the current state matches the expected solution
   */
  check: (current_state: any) => Promise<boolean>;

  /**
   * Get the encoding of a state (for debugging)
   */
  encode: (state: any) => Promise<string>;
}

/**
 * Create a solution checker for a puzzle
 */
export function useSolutionChecker(config: SolutionCheckerConfig): SolutionCheckerReturn {
  const {
    type,
    solution_hash,
    expected_solution,
    positive_values = [],
    custom_encoder,
  } = config;

  /**
   * Encode a cell-grid state using run-length encoding
   */
  async function encode_cell_grid(board: number[][]): Promise<string> {
    if (!board || board.length === 0) return "0";

    const encoding_parts: string[] = [];
    const positive_positions: Array<[number, number, string]> = [];
    const cols = board[0]?.length || 0;

    // Find all positive state positions
    for (let row = 0; row < board.length; row++) {
      for (let col = 0; col < board[row].length; col++) {
        const cell_value = board[row][col];
        if (positive_values.includes(cell_value)) {
          // For single positive value, use "1"; for multiple (Sudoku), use actual value
          const state_char =
            positive_values.length === 1 ? "1" : cell_value.toString();
          positive_positions.push([row, col, state_char]);
        }
      }
    }

    if (positive_positions.length === 0) {
      return "0";
    }

    // Encode leading empty cells before first positive state
    const [first_row, first_col] = positive_positions[0];
    const leading_gap = first_row * cols + first_col;

    if (leading_gap > 0) {
      encoding_parts.push(encode_gap(leading_gap));
    }

    // Build run-length encoding
    for (let i = 0; i < positive_positions.length; i++) {
      const [row, col, state_char] = positive_positions[i];
      encoding_parts.push(state_char);

      if (i < positive_positions.length - 1) {
        const [next_row, next_col] = positive_positions[i + 1];
        const pos1 = row * cols + col;
        const pos2 = next_row * cols + next_col;
        const gap_count = pos2 - pos1 - 1;

        if (gap_count > 0) {
          encoding_parts.push(encode_gap(gap_count));
        }
      }
    }

    return encoding_parts.join("");
  }

  /**
   * Encode a gap between positions
   */
  function encode_gap(gap: number): string {
    if (gap <= 26) {
      // Convert to letter (a=1, b=2, ..., z=26)
      return String.fromCharCode("a".charCodeAt(0) + gap - 1);
    } else {
      // For larger gaps, use #N notation
      return `#${gap}`;
    }
  }

  /**
   * Encode state based on strategy type
   */
  async function encode(state: any): Promise<string> {
    switch (type) {
      case "cell-grid":
        return encode_cell_grid(state as number[][]);

      case "connection":
        // Connection encoding should be provided via custom_encoder
        if (custom_encoder) {
          return await custom_encoder(state);
        }
        throw new Error(
          "useSolutionChecker: connection type requires custom_encoder"
        );

      case "custom":
        if (!custom_encoder) {
          throw new Error(
            "useSolutionChecker: custom type requires custom_encoder"
          );
        }
        return await custom_encoder(state);

      default:
        throw new Error(`useSolutionChecker: unknown type "${type}"`);
    }
  }

  /**
   * Check if current state matches expected solution
   */
  async function check(current_state: any): Promise<boolean> {
    try {
      const current_encoding = await encode(current_state);

      // If we have a solution hash, compare against it
      if (solution_hash) {
        return current_encoding === solution_hash;
      }

      // If we have an expected solution, encode it and compare
      if (expected_solution) {
        const expected_encoding = await encode(expected_solution);
        return current_encoding === expected_encoding;
      }

      // No solution to compare against
      console.warn("useSolutionChecker: no solution_hash or expected_solution provided");
      return false;
    } catch (error) {
      console.error("useSolutionChecker: validation error", error);
      return false;
    }
  }

  return {
    check,
    encode,
  };
}

/**
 * Helper to create a bridge encoder for Hashi-like games
 */
export function create_bridge_encoder<TBridge extends { from: { row: number; col: number }; to: { row: number; col: number }; count?: number }>(
): (bridges: TBridge[]) => string {
  return (bridges: TBridge[]) => {
    if (!bridges || bridges.length === 0) return "0";

    // Sort bridges for consistent encoding
    const sorted = [...bridges].sort((a, b) => {
      // Sort by from position first, then by to position
      const a_from = a.from.row * 1000 + a.from.col;
      const b_from = b.from.row * 1000 + b.from.col;
      if (a_from !== b_from) return a_from - b_from;

      const a_to = a.to.row * 1000 + a.to.col;
      const b_to = b.to.row * 1000 + b.to.col;
      return a_to - b_to;
    });

    // Encode as: r1,c1-r2,c2:count;r1,c1-r2,c2:count;...
    return sorted
      .map((b) => `${b.from.row},${b.from.col}-${b.to.row},${b.to.col}:${b.count ?? 1}`)
      .join(";");
  };
}
