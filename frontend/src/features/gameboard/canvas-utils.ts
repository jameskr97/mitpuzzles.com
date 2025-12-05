/**
 * Canvas utility functions for puzzle rendering
 */

export interface RegionBorderOptions {
  border_width?: number;
  border_color?: string;
}

/**
 * Draw thick borders around regions where adjacent cells belong to different regions.
 *
 * @param ctx - Canvas 2D rendering context
 * @param row - Current cell row
 * @param col - Current cell column
 * @param x - X coordinate of cell
 * @param y - Y coordinate of cell
 * @param size - Cell size
 * @param rows - Total rows in grid
 * @param cols - Total columns in grid
 * @param region_map - 2D array where each cell contains its region ID
 * @param options - Optional styling options
 */
export function draw_region_borders(
  ctx: CanvasRenderingContext2D,
  row: number,
  col: number,
  x: number,
  y: number,
  size: number,
  rows: number,
  cols: number,
  region_map: number[][],
  options: RegionBorderOptions = {}
): void {
  const { border_width = 3, border_color = "#000000" } = options;

  ctx.strokeStyle = border_color;
  ctx.lineWidth = border_width;
  const current_region = region_map[row]?.[col];
  const overlap = border_width / 2;

  // Top border - different region above or edge
  if (row === 0 || region_map[row - 1]?.[col] !== current_region) {
    ctx.beginPath();
    ctx.moveTo(x - overlap, y);
    ctx.lineTo(x + size + overlap, y);
    ctx.stroke();
  }

  // Bottom border - different region below or edge
  if (row === rows - 1 || region_map[row + 1]?.[col] !== current_region) {
    ctx.beginPath();
    ctx.moveTo(x - overlap, y + size);
    ctx.lineTo(x + size + overlap, y + size);
    ctx.stroke();
  }

  // Left border - different region to left or edge
  if (col === 0 || region_map[row]?.[col - 1] !== current_region) {
    ctx.beginPath();
    ctx.moveTo(x, y - overlap);
    ctx.lineTo(x, y + size + overlap);
    ctx.stroke();
  }

  // Right border - different region to right or edge
  if (col === cols - 1 || region_map[row]?.[col + 1] !== current_region) {
    ctx.beginPath();
    ctx.moveTo(x + size, y - overlap);
    ctx.lineTo(x + size, y + size + overlap);
    ctx.stroke();
  }
}
