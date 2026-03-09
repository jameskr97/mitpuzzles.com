import type { GridConfig, TextOptions } from './canvas-types';

/**
 * Canvas renderer with high-DPI support and drawing primitives.
 *
 * Handles:
 * - High-DPI display scaling
 * - Basic shape rendering (rectangles, lines)
 * - Text rendering with proper alignment
 * - Grid rendering with optional major lines
 */
export class CanvasRenderer {
  private canvas: HTMLCanvasElement;
  private ctx: CanvasRenderingContext2D;
  private dpr: number = 1;

  constructor(canvas: HTMLCanvasElement) {
    this.canvas = canvas;
    const context = canvas.getContext('2d', { alpha: true });

    if (!context) {
      throw new Error('Failed to get 2D context from canvas');
    }

    this.ctx = context;

    // Disable anti-aliasing for crisp rendering
    this.ctx.imageSmoothingEnabled = false;

    this.setupHighDPI();
  }

  /**
   * Setup canvas for high-DPI displays (retina, etc.)
   * Ensures crisp rendering on all displays
   */
  setupHighDPI(): void {
    this.dpr = window.devicePixelRatio || 1;
    const scale = window.visualViewport?.scale || 1;

    const rect = this.canvas.getBoundingClientRect();

    const newWidth = Math.round(rect.width * this.dpr * scale);
    const newHeight = Math.round(rect.height * this.dpr * scale);

    // Only resize the pixel buffer if dimensions actually changed
    // (setting canvas.width/height clears the canvas even if value is unchanged)
    if (this.canvas.width !== newWidth || this.canvas.height !== newHeight) {
      this.canvas.width = newWidth;
      this.canvas.height = newHeight;
    }

    // Reset transform to avoid stacking when called multiple times
    this.ctx.setTransform(1, 0, 0, 1, 0, 0);

    // Scale context to match device pixel ratio AND zoom
    this.ctx.scale(this.dpr * scale, this.dpr * scale);

    // Re-disable anti-aliasing after transform reset
    this.ctx.imageSmoothingEnabled = false;
  }

  /**
   * Get the underlying canvas context
   */
  getContext(): CanvasRenderingContext2D {
    return this.ctx;
  }

  /**
   * Clear the entire canvas
   */
  clear(): void {
    const rect = this.canvas.getBoundingClientRect();
    this.ctx.clearRect(0, 0, rect.width, rect.height);
  }

  /**
   * Draw a filled rectangle
   */
  drawRect(x: number, y: number, w: number, h: number, color: string): void {
    this.ctx.fillStyle = color;
    this.ctx.fillRect(x, y, w, h);
  }

  /**
   * Draw a line between two points
   * Automatically adds 0.5 offset for pixel-perfect lines
   */
  drawLine(
    x1: number,
    y1: number,
    x2: number,
    y2: number,
    color: string,
    thickness: number = 1
  ): void {
    this.ctx.beginPath();
    this.ctx.moveTo(x1 + 0.5, y1 + 0.5);
    this.ctx.lineTo(x2 + 0.5, y2 + 0.5);
    this.ctx.strokeStyle = color;
    this.ctx.lineWidth = thickness;
    this.ctx.stroke();

    // Draw endpoints explicitly for pixel-perfect rendering
    this.ctx.fillStyle = color;
    this.ctx.fillRect(x1, y1, 1, 1);
    this.ctx.fillRect(x2, y2, 1, 1);
  }

  /**
   * Draw text with specified options
   */
  drawText(x: number, y: number, text: string, options: TextOptions): void {
    const {
      font = 'sans-serif',
      size,
      align = 'left',
      valign = 'top',
      color,
      weight = 'normal'
    } = options;

    this.ctx.font = `${weight} ${size}px ${font}`;
    this.ctx.fillStyle = color;
    this.ctx.textAlign = align;
    this.ctx.textBaseline = valign === 'middle' ? 'middle' : valign === 'bottom' ? 'bottom' : 'top';
    this.ctx.fillText(text, x, y);
  }

  /**
   * Draw a complete grid with cells, borders, and optional major lines
   *
   * @param rows - Number of rows
   * @param cols - Number of columns
   * @param cellSize - Size of each cell in pixels
   * @param config - Grid configuration
   */
  drawGrid(
    rows: number,
    cols: number,
    cellSize: number,
    config: GridConfig
  ): void {
    const {
      gap = 1,
      borderThickness = 1,
      majorGridEvery,
      majorGridThickness = 3
    } = config;

    const totalWidth = cols * cellSize + (cols + 1) * gap;
    const totalHeight = rows * cellSize + (rows + 1) * gap;

    // Draw horizontal lines
    for (let i = 0; i <= rows; i++) {
      const y = i * (cellSize + gap);
      const isMajor = majorGridEvery && i % majorGridEvery === 0;
      const thickness = isMajor ? majorGridThickness : borderThickness;

      // For thicker lines, center them on the grid line position
      const offset = thickness > 1 ? Math.floor((thickness - 1) / 2) : 0;

      this.drawLine(
        gap / 2,
        y - offset,
        totalWidth - gap / 2,
        y - offset,
        'currentColor',  // Will be set via CSS or context
        thickness
      );
    }

    // Draw vertical lines
    for (let i = 0; i <= cols; i++) {
      const x = i * (cellSize + gap);
      const isMajor = majorGridEvery && i % majorGridEvery === 0;
      const thickness = isMajor ? majorGridThickness : borderThickness;

      const offset = thickness > 1 ? Math.floor((thickness - 1) / 2) : 0;

      this.drawLine(
        x - offset,
        gap / 2,
        x - offset,
        totalHeight - gap / 2,
        'currentColor',
        thickness
      );
    }
  }

  /**
   * Set the global fill style
   */
  setFillStyle(color: string): void {
    this.ctx.fillStyle = color;
  }

  /**
   * Set the global stroke style
   */
  setStrokeStyle(color: string): void {
    this.ctx.strokeStyle = color;
  }

  /**
   * Save the current canvas state
   */
  save(): void {
    this.ctx.save();
  }

  /**
   * Restore the previous canvas state
   */
  restore(): void {
    this.ctx.restore();
  }

  /**
   * Set clipping region
   */
  clip(x: number, y: number, w: number, h: number): void {
    this.ctx.save();
    this.ctx.beginPath();
    this.ctx.rect(x, y, w, h);
    this.ctx.clip();
  }

  /**
   * Restore from clipping region (same as restore)
   */
  unclip(): void {
    this.ctx.restore();
  }
}
