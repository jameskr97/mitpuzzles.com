import type { PuzzleState } from "@/core/games/types/puzzle-types.ts";

/**
 * function type for rendering individual cells on the canvas.
 *
 * @param ctx - Canvas 2D rendering context
 * @param row - Row index of the cell
 * @param col - Column index of the cell
 * @param x - X coordinate of top-left corner (in logical pixels)
 * @param y - Y coordinate of top-left corner (in logical pixels)
 * @param size - Size of the cell (in logical pixels)
 * @param state - Current puzzle state
 */
export type CellRenderer = (
  ctx: CanvasRenderingContext2D,
  row: number,
  col: number,
  x: number,
  y: number,
  size: number,
  state: PuzzleState
) => void;

/** configuration for grid renderin */
export interface GridConfig {
  /** Gap between cells in pixels (default: 1) */
  gap: number;

  /** Thickness of regular grid lines in pixels (default: 1) */
  borderThickness?: number;

  /** Draw thicker lines every N rows/columns (e.g., 3 for Sudoku boxes) */
  majorGridEvery?: number;

  /** Thickness of major grid lines in pixels (default: 3) */
  majorGridThickness?: number;

  /** Color for regular grid lines (default: '#cccccc') */
  gridColor?: string;

  /** Color for major grid lines (default: '#808080') */
  majorGridColor?: string;
}

/** theme colors for canvas rendering */
export interface CanvasTheme {
  /** Background color for cells */
  background: string;

  /** Regular grid line color */
  grid: string;

  /** Major grid line color (every Nth row/col) */
  majorGrid: string;

  /** Text color for user-entered values */
  text: string;

  /** Text color for prefilled/immutable values */
  prefilled: string;

  /** Error/violation highlight color */
  error: string;

  /** Cursor/selection highlight color */
  cursor: string;

  // Game-specific colors

  /** Wall/black cell color (Lightup, Mosaic) */
  wall: string;

  /** Lit cell background color (Lightup) */
  lit: string;

  /** Green/grass color (Tents) */
  green: string;

  /** Gray/unmarked color (Mosaic) */
  gray: string;

  /** Blue/sum color (Kakurasu) */
  blue: string;

  /** Hint/clue color */
  hint: string;
}

/**
 * Text rendering options
 */
export interface TextOptions {
  /** Font family */
  font?: string;

  /** Font size in pixels */
  size: number;

  /** Horizontal alignment */
  align?: 'left' | 'center' | 'right';

  /** Vertical alignment */
  valign?: 'top' | 'middle' | 'bottom';

  /** Text color */
  color: string;

  /** Font weight */
  weight?: 'normal' | 'bold' | 'bolder' | number;
}

/**
 * Cell coordinate result from click detection
 */
export interface CellCoordinate {
  row: number;
  col: number;
  zone: 'game' | 'topGutter' | 'leftGutter' | 'rightGutter' | 'bottomGutter';
}

/**
 * Rectangle definition
 */
export interface Rectangle {
  x: number;
  y: number;
  w: number;
  h: number;
}
