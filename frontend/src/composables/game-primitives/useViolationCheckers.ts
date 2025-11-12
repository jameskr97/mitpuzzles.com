/**
 * Shared violation checking utilities for puzzle games
 */

/** Orthogonal directions (up, down, left, right) */
export const ORTHOGONAL_DIRECTIONS: [number, number][] = [
  [-1, 0], [1, 0], [0, -1], [0, 1]
];

/** All 8 directions including diagonals */
export const ALL_DIRECTIONS: [number, number][] = [
  [-1, -1], [-1, 0], [-1, 1],
  [0, -1],           [0, 1],
  [1, -1],  [1, 0],  [1, 1]
];

/**
 * Count adjacent cells that match target values
 */
export function count_adjacent(
  board: number[][],
  row: number,
  col: number,
  target_values: number[],
  directions: [number, number][] = ORTHOGONAL_DIRECTIONS
): number {
  const rows = board.length;
  const cols = board[0]?.length ?? 0;
  let count = 0;

  for (const [dr, dc] of directions) {
    const nr = row + dr;
    const nc = col + dc;
    if (nr >= 0 && nr < rows && nc >= 0 && nc < cols) {
      if (target_values.includes(board[nr][nc])) {
        count++;
      }
    }
  }

  return count;
}

/**
 * Count cells in a row that match target values
 */
export function count_in_row(
  board: number[][],
  row: number,
  target_values: number[]
): number {
  return board[row]?.filter(cell => target_values.includes(cell)).length ?? 0;
}

/**
 * Count cells in a column that match target values
 */
export function count_in_col(
  board: number[][],
  col: number,
  target_values: number[]
): number {
  let count = 0;
  for (let r = 0; r < board.length; r++) {
    if (target_values.includes(board[r]?.[col])) {
      count++;
    }
  }
  return count;
}

/**
 * Get weighted sum in a row (value = col_index + 1, like Kakurasu)
 */
export function weighted_sum_row(
  board: number[][],
  row: number,
  positive_values: number[]
): number {
  let sum = 0;
  const row_data = board[row];
  if (!row_data) return 0;

  for (let c = 0; c < row_data.length; c++) {
    if (positive_values.includes(row_data[c])) {
      sum += c + 1;
    }
  }
  return sum;
}

/**
 * Get weighted sum in a column (value = row_index + 1, like Kakurasu)
 */
export function weighted_sum_col(
  board: number[][],
  col: number,
  positive_values: number[]
): number {
  let sum = 0;
  for (let r = 0; r < board.length; r++) {
    if (positive_values.includes(board[r]?.[col])) {
      sum += r + 1;
    }
  }
  return sum;
}

/**
 * Check if all cells in a row are one of the given values (e.g., all crossed out)
 */
export function all_cells_in_row(
  board: number[][],
  row: number,
  target_values: number[]
): boolean {
  return board[row]?.every(cell => target_values.includes(cell)) ?? false;
}

/**
 * Check if all cells in a column are one of the given values
 */
export function all_cells_in_col(
  board: number[][],
  col: number,
  target_values: number[]
): boolean {
  for (let r = 0; r < board.length; r++) {
    if (!target_values.includes(board[r]?.[col])) {
      return false;
    }
  }
  return true;
}

// ============ Region utilities ============

/**
 * Get all cells belonging to a specific region
 */
export function get_region_cells(
  region_map: number[][],
  region_id: number
): [number, number][] {
  const cells: [number, number][] = [];
  for (let r = 0; r < region_map.length; r++) {
    for (let c = 0; c < (region_map[r]?.length ?? 0); c++) {
      if (region_map[r][c] === region_id) {
        cells.push([r, c]);
      }
    }
  }
  return cells;
}

/**
 * Get all unique region IDs from a region map
 */
export function get_all_region_ids(region_map: number[][]): Set<number> {
  const regions = new Set<number>();
  for (let r = 0; r < region_map.length; r++) {
    for (let c = 0; c < (region_map[r]?.length ?? 0); c++) {
      regions.add(region_map[r][c]);
    }
  }
  return regions;
}

/**
 * Get region ID for a specific cell
 */
export function get_region_at(
  region_map: number[][],
  row: number,
  col: number
): number {
  return region_map[row]?.[col] ?? -1;
}

/**
 * Check if two cells are in the same region
 */
export function same_region(
  region_map: number[][],
  r1: number,
  c1: number,
  r2: number,
  c2: number
): boolean {
  return get_region_at(region_map, r1, c1) === get_region_at(region_map, r2, c2);
}

/**
 * Count cells with target values in a specific region
 */
export function count_in_region(
  board: number[][],
  region_map: number[][],
  region_id: number,
  target_values: number[]
): number {
  const cells = get_region_cells(region_map, region_id);
  return cells.filter(([r, c]) => target_values.includes(board[r]?.[c])).length;
}
