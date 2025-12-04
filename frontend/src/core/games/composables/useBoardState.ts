/**
 * useBoardState - Core 2D grid state management
 *
 * Provides reactive board state with cell manipulation methods.
 * Mode-agnostic: works in both freeplay and experiment contexts.
 */
import { ref, computed, type Ref, type ComputedRef } from "vue";
import type { Cell } from "@/core/games/types/puzzle-types.ts";

export interface BoardStateReturn {
  /** Current board state (reactive) */
  board: Ref<number[][]>;

  /** Initial state (immutable reference for reset) */
  initial_state: Readonly<number[][]>;

  /** Number of rows */
  rows: ComputedRef<number>;

  /** Number of columns */
  cols: ComputedRef<number>;

  /** Set a single cell value */
  set_cell: (row: number, col: number, value: number) => void;

  /** Get a single cell value */
  get_cell: (row: number, col: number) => number;

  /** Clear board back to initial state */
  clear: () => void;

  /** Check if a cell can be modified (not part of initial puzzle) */
  is_cell_editable: (row: number, col: number) => boolean;

  /** Get immutable cells matrix (1 = immutable, 0 = editable) */
  immutable_cells: ComputedRef<number[][]>;
}

export interface BoardStateOptions {
  /**
   * Function to determine if a cell is editable based on its initial value.
   * Default: cell is editable if initial value equals empty_value
   */
  is_editable?: (initial_value: number, row: number, col: number) => boolean;

  /**
   * Value that represents an empty/editable cell in the initial state.
   * Default: -1 (common research format for empty cells)
   */
  empty_value?: number;
}

/**
 * Create reactive board state for a puzzle
 *
 * @param initial - Initial board state (2D array)
 * @param saved - Optional saved state to restore (for freeplay persistence)
 * @param options - Configuration options
 */
export function useBoardState(
  initial: number[][],
  saved?: number[][] | null,
  options: BoardStateOptions = {}
): BoardStateReturn {
  const { empty_value = -1, is_editable } = options;

  // Deep clone initial state to prevent mutations
  const initial_state: Readonly<number[][]> = JSON.parse(JSON.stringify(initial));

  // Current board state - start from saved or initial
  const board = ref<number[][]>(
    saved ? JSON.parse(JSON.stringify(saved)) : JSON.parse(JSON.stringify(initial))
  );

  // Computed dimensions
  const rows = computed(() => board.value.length);
  const cols = computed(() => (board.value[0]?.length ?? 0));

  // Default editability check
  const default_is_editable = (initial_value: number) => initial_value === empty_value;
  const editability_check = is_editable ?? default_is_editable;

  /**
   * Check if a cell is editable (not part of the initial puzzle)
   */
  function is_cell_editable(row: number, col: number): boolean {
    if (row < 0 || row >= rows.value || col < 0 || col >= cols.value) {
      return false;
    }
    return editability_check(initial_state[row][col], row, col);
  }

  /**
   * Immutable cells matrix for rendering
   */
  const immutable_cells = computed<number[][]>(() => {
    const result: number[][] = [];
    for (let r = 0; r < rows.value; r++) {
      const row_data: number[] = [];
      for (let c = 0; c < cols.value; c++) {
        row_data.push(is_cell_editable(r, c) ? 0 : 1);
      }
      result.push(row_data);
    }
    return result;
  });

  /**
   * Set a single cell value
   */
  function set_cell(row: number, col: number, value: number): void {
    if (row < 0 || row >= rows.value || col < 0 || col >= cols.value) {
      console.warn(`set_cell: Invalid position (${row}, ${col})`);
      return;
    }
    board.value[row][col] = value;
  }

  /**
   * Get a single cell value
   */
  function get_cell(row: number, col: number): number {
    if (row < 0 || row >= rows.value || col < 0 || col >= cols.value) {
      console.warn(`get_cell: Invalid position (${row}, ${col})`);
      return -1;
    }
    return board.value[row][col];
  }

  /**
   * Clear board back to initial state
   */
  function clear(): void {
    board.value = JSON.parse(JSON.stringify(initial_state));
  }

  return {
    board,
    initial_state,
    rows,
    cols,
    set_cell,
    get_cell,
    clear,
    is_cell_editable,
    immutable_cells,
  };
}
