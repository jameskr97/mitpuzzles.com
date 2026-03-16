import type { GridConfig, TextOptions, CellBox } from './canvas-types';

export interface CellTextStyle {
  color?: string;
  sizeFactor?: number;
  sizePx?: number;
  weight?: 'normal' | 'bold';
  font?: string;
  offsetY?: number;
}

export interface RegionBorderOptions {
  border_width?: number;
  border_color?: string;
}

/**
 * Canvas renderer with high-DPI support and drawing primitives.
 * - setting up high-dpi display scaling
 * - shape/text/grid rendering
 * - is cell aware
 */
export class CanvasRenderer {
  private canvas: HTMLCanvasElement;
  readonly ctx: CanvasRenderingContext2D;
  private dpr: number = 1;

  constructor(canvas: HTMLCanvasElement) {
    this.canvas = canvas;
    const context = canvas.getContext("2d", { alpha: true });
    if (!context) {
      throw new Error("Failed to get 2D context from canvas");
    }

    this.ctx = context;
    this.ctx.imageSmoothingEnabled = false; // disable anti-aliasing for crisp rendering
    this.setupHighDPI();
  }

  /**
   * Setup canvas for high-DPI displays
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

  /** cell aware rendering methods **/
  fillCell(cell: CellBox, color: string, overflow: number = 0): void {
    this.ctx.fillStyle = color;
    this.ctx.fillRect(cell.x, cell.y, cell.size + overflow, cell.size + overflow);
  }

  strokeCell(cell: CellBox, color: string, lineWidth: number = 1): void {
    this.ctx.strokeStyle = color;
    this.ctx.lineWidth = lineWidth;
    this.ctx.strokeRect(cell.x, cell.y, cell.size, cell.size);
  }

  strokeRectInset(cell: CellBox, color: string, inset: number, lineWidth: number = 3): void {
    this.ctx.strokeStyle = color;
    this.ctx.lineWidth = lineWidth;
    this.ctx.strokeRect(cell.x + inset, cell.y + inset, cell.size - inset * 2, cell.size - inset * 2);
  }

  textCentered(cell: CellBox, text: string, style?: CellTextStyle): void {
    const s = style ?? {};
    const fontSize = s.sizePx ?? (cell.size * (s.sizeFactor ?? 0.6));
    const weight = s.weight ?? 'bold';
    const font = s.font ?? 'sans-serif';
    this.ctx.font = `${weight} ${fontSize}px ${font}`;
    this.ctx.fillStyle = s.color ?? '#000000';
    this.ctx.textAlign = 'center';
    this.ctx.textBaseline = 'middle';
    this.ctx.fillText(text, cell.cx, cell.cy + (s.offsetY ?? 0));
  }

  imageCell(cell: CellBox, img: HTMLImageElement): void {
    this.ctx.drawImage(img, cell.x, cell.y, cell.size, cell.size);
  }

  imageCentered(cell: CellBox, img: HTMLImageElement, scaleFactor: number = 0.67): void {
    const imgSize = cell.size * scaleFactor;
    const offset = (cell.size - imgSize) / 2;
    this.ctx.drawImage(img, cell.x + offset, cell.y + offset, imgSize, imgSize);
  }

  crossMark(cell: CellBox, image: HTMLImageElement | null, options?: {
    imageScale?: number;
    linePadding?: number;
    lineColor?: string;
    lineWidth?: number;
  }): void {
    const o = options ?? {};
    if (image) {
      this.imageCentered(cell, image, o.imageScale ?? 0.67);
    } else {
      const padding = cell.size * (o.linePadding ?? 0.17);
      this.ctx.strokeStyle = o.lineColor ?? '#000000';
      this.ctx.lineWidth = o.lineWidth ?? 1;
      this.ctx.beginPath();
      this.ctx.moveTo(cell.x + padding, cell.y + padding);
      this.ctx.lineTo(cell.x + cell.size - padding, cell.y + cell.size - padding);
      this.ctx.moveTo(cell.x + cell.size - padding, cell.y + padding);
      this.ctx.lineTo(cell.x + padding, cell.y + cell.size - padding);
      this.ctx.stroke();
    }
  }

  filledSquare(cell: CellBox, color: string, inset: number = 2): void {
    const i2 = inset * 2;
    this.ctx.fillStyle = color;
    this.ctx.fillRect(cell.x + inset, cell.y + inset, cell.size - i2, cell.size - i2);
  }

  regionBorders(
    cell: CellBox,
    row: number, col: number,
    rows: number, cols: number,
    regionMap: number[][],
    options?: RegionBorderOptions,
  ): void {
    const bw = options?.border_width ?? 3;
    const bc = options?.border_color ?? '#000000';
    this.ctx.strokeStyle = bc;
    this.ctx.lineWidth = bw;
    const currentRegion = regionMap[row]?.[col];
    const overlap = bw / 2;
    const { x, y, size } = cell;

    if (row === 0 || regionMap[row - 1]?.[col] !== currentRegion) {
      this.ctx.beginPath();
      this.ctx.moveTo(x - overlap, y);
      this.ctx.lineTo(x + size + overlap, y);
      this.ctx.stroke();
    }
    if (row === rows - 1 || regionMap[row + 1]?.[col] !== currentRegion) {
      this.ctx.beginPath();
      this.ctx.moveTo(x - overlap, y + size);
      this.ctx.lineTo(x + size + overlap, y + size);
      this.ctx.stroke();
    }
    if (col === 0 || regionMap[row]?.[col - 1] !== currentRegion) {
      this.ctx.beginPath();
      this.ctx.moveTo(x, y - overlap);
      this.ctx.lineTo(x, y + size + overlap);
      this.ctx.stroke();
    }
    if (col === cols - 1 || regionMap[row]?.[col + 1] !== currentRegion) {
      this.ctx.beginPath();
      this.ctx.moveTo(x + size, y - overlap);
      this.ctx.lineTo(x + size, y + size + overlap);
      this.ctx.stroke();
    }
  }

  withFilter(filter: string, fn: () => void): void {
    const prev = this.ctx.filter;
    this.ctx.filter = filter;
    fn();
    this.ctx.filter = prev;
  }
}
