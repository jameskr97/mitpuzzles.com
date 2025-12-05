<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch, computed, nextTick } from 'vue';
import { CanvasRenderer } from './canvas-renderer';
import type { CellRenderer, CellCoordinate } from './canvas-types';


const props = withDefaults(
  defineProps<{
    /** Number of rows in the grid */
    rows: number;
    /** Number of columns in the grid */
    cols: number;
    /** Puzzle state containing board data */
    state: any;
    /** Function to render each cell */
    cellRenderer: CellRenderer;
    /** Size of each cell in pixels (auto-calculated if not provided) */
    cellSize?: number;
    /** Scale factor for the entire board (default: 1) */
    scale?: number;
    /** Gap between cells in pixels (default: 1) - deprecated, use insideBorderThickness */
    gap?: number;
    /** Color for grid lines (default: '#cccccc') */
    gridColor?: string;
    /** Draw thicker lines every N rows/columns (e.g., 3 for Sudoku boxes) */
    majorGridEvery?: number;
    /** Thickness of major grid lines in pixels (default: 3) */
    majorGridThickness?: number;
    /** Color for major grid lines (default: '#808080') */
    majorGridColor?: string;
    /** Number of gutter rows at top (default: 0) */
    gutterTop?: number;
    /** Number of gutter columns at left (default: 0) */
    gutterLeft?: number;
    /** Number of gutter columns at right (default: 0) */
    gutterRight?: number;
    /** Number of gutter rows at bottom (default: 0) */
    gutterBottom?: number;
    /** Thickness of outside borders (perimeter + zone boundaries) in pixels */
    outsideBorderThickness?: number;
    /** Color for outside borders (default: '#000000') */
    outsideBorderColor?: string;
    /** Thickness of inside borders (between cells in same zone) in pixels */
    insideBorderThickness?: number;
    /** Draw inside borders in top gutter: 'none', 'horizontal', 'vertical', 'both' */
    gutterTopInsideBorders?: 'none' | 'horizontal' | 'vertical' | 'both';
    /** Draw inside borders in left gutter: 'none', 'horizontal', 'vertical', 'both' */
    gutterLeftInsideBorders?: 'none' | 'horizontal' | 'vertical' | 'both';
    /** Draw inside borders in right gutter: 'none', 'horizontal', 'vertical', 'both' */
    gutterRightInsideBorders?: 'none' | 'horizontal' | 'vertical' | 'both';
    /** Draw inside borders in bottom gutter: 'none', 'horizontal', 'vertical', 'both' */
    gutterBottomInsideBorders?: 'none' | 'horizontal' | 'vertical' | 'both';
    /** Draw outside border around top gutter */
    drawGutterTopOutsideBorder?: boolean;
    /** Draw outside border around left gutter */
    drawGutterLeftOutsideBorder?: boolean;
    /** Draw outside border around right gutter */
    drawGutterRightOutsideBorder?: boolean;
    /** Draw outside border around bottom gutter */
    drawGutterBottomOutsideBorder?: boolean;
    /** Enable double-click to export as PNG (dev utility) */
    enableExport?: boolean;
    /** Whether to draw grid lines (default: true) */
    drawGridLines?: boolean;
  }>(),
  {
    scale: 1,
    gap: 1,
    gridColor: 'black',
    majorGridThickness: 3,
    majorGridColor: '#808080',
    gutterTop: 0,
    gutterLeft: 0,
    gutterRight: 0,
    gutterBottom: 0,
    outsideBorderThickness: 5,
    outsideBorderColor: '#000000',
    insideBorderThickness: 1,
    gutterTopInsideBorders: 'both',
    gutterLeftInsideBorders: 'both',
    gutterRightInsideBorders: 'both',
    gutterBottomInsideBorders: 'both',
    drawGutterTopOutsideBorder: true,
    drawGutterLeftOutsideBorder: true,
    drawGutterRightOutsideBorder: true,
    drawGutterBottomOutsideBorder: true,
    enableExport: false,
    drawGridLines: true
  }
);

const emit = defineEmits<{
  'cell-click': [coord: CellCoordinate];
  'cell-mousedown': [coord: CellCoordinate, event: MouseEvent];
  'cell-mouseup': [coord: CellCoordinate, event: MouseEvent];
  'cell-enter': [coord: CellCoordinate, event: MouseEvent];
  'cell-leave': [coord: CellCoordinate, event: MouseEvent];
  'cell-focus': [coord: CellCoordinate, event: MouseEvent];
  'board-enter': [event: MouseEvent];
  'board-leave': [event: MouseEvent];
}>();

const canvasRef = ref<HTMLCanvasElement | null>(null);
const containerRef = ref<HTMLDivElement | null>(null);
let renderer: CanvasRenderer | null = null;
let containerResizeObserver: ResizeObserver | null = null;

// Reactive trigger for container size changes
const containerSize = ref({ width: 0, height: 0 });

// Mouse state tracking for event handling
let last_mousedown_cell: CellCoordinate | null = null;
let last_hover_cell: CellCoordinate | null = null;
let focused_cell: CellCoordinate | null = null;

// Computed cell size with auto-calculation
const computedCellSize = computed(() => {
  if (props.cellSize) {
    return props.cellSize * props.scale;
  }

  // Auto-calculate based on container size
  // Use containerSize.value to make this reactive to container resizes
  const containerWidth = containerSize.value.width || 500;
  const containerHeight = containerSize.value.height || 500;

  const outside = props.outsideBorderThickness!;
  const inside = props.insideBorderThickness!;

  // Calculate horizontal borders
  // Outside: perimeter (2) + zone transitions
  const outsideBordersH = 2 +
    (props.gutterLeft > 0 ? 1 : 0) +
    (props.gutterRight > 0 ? 1 : 0);

  // Inside: within each zone (cells - 1 per zone)
  const insideBordersH =
    Math.max(0, props.gutterLeft - 1) +
    Math.max(0, props.cols - 1) +
    Math.max(0, props.gutterRight - 1);

  const totalCols = props.gutterLeft + props.cols + props.gutterRight;

  // Calculate vertical borders
  const outsideBordersV = 2 +
    (props.gutterTop > 0 ? 1 : 0) +
    (props.gutterBottom > 0 ? 1 : 0);

  const insideBordersV =
    Math.max(0, props.gutterTop - 1) +
    Math.max(0, props.rows - 1) +
    Math.max(0, props.gutterBottom - 1);

  const totalRows = props.gutterTop + props.rows + props.gutterBottom;

  // Calculate cell size that fits both dimensions
  const cellWidth = (containerWidth - outsideBordersH * outside - insideBordersH * inside) / totalCols;
  const cellHeight = (containerHeight - outsideBordersV * outside - insideBordersV * inside) / totalRows;

  return Math.floor(Math.min(cellWidth, cellHeight) * props.scale);
});

// Computed board dimensions (including gutters and borders)
const boardWidth = computed(() => {
  const outside = props.outsideBorderThickness!;
  const inside = props.insideBorderThickness!;
  const totalCols = props.cols + props.gutterLeft + props.gutterRight;

  const outsideBordersH = 2 +
    (props.gutterLeft > 0 ? 1 : 0) +
    (props.gutterRight > 0 ? 1 : 0);

  const insideBordersH =
    Math.max(0, props.gutterLeft - 1) +
    Math.max(0, props.cols - 1) +
    Math.max(0, props.gutterRight - 1);

  return totalCols * computedCellSize.value +
    outsideBordersH * outside +
    insideBordersH * inside;
});

const boardHeight = computed(() => {
  const outside = props.outsideBorderThickness!;
  const inside = props.insideBorderThickness!;
  const totalRows = props.rows + props.gutterTop + props.gutterBottom;

  const outsideBordersV = 2 +
    (props.gutterTop > 0 ? 1 : 0) +
    (props.gutterBottom > 0 ? 1 : 0);

  const insideBordersV =
    Math.max(0, props.gutterTop - 1) +
    Math.max(0, props.rows - 1) +
    Math.max(0, props.gutterBottom - 1);

  return totalRows * computedCellSize.value +
    outsideBordersV * outside +
    insideBordersV * inside;
});

// Starting position for the main grid (after outside border and gutters)
const gridStartX = computed(() => {
  const outside = props.outsideBorderThickness!;
  const inside = props.insideBorderThickness!;
  const cellSize = computedCellSize.value;

  let x = outside; // Start after left outside border

  if (props.gutterLeft > 0) {
    // Add left gutter zone
    x += props.gutterLeft * cellSize;
    x += Math.max(0, props.gutterLeft - 1) * inside;
    // Add outside border between left gutter and main grid
    x += outside;
  }

  return x;
});

const gridStartY = computed(() => {
  const outside = props.outsideBorderThickness!;
  const inside = props.insideBorderThickness!;
  const cellSize = computedCellSize.value;

  let y = outside; // Start after top outside border

  if (props.gutterTop > 0) {
    // Add top gutter zone
    y += props.gutterTop * cellSize;
    y += Math.max(0, props.gutterTop - 1) * inside;
    // Add outside border between top gutter and main grid
    y += outside;
  }

  return y;
});

/**
 * Initialize the canvas and renderer
 */
function setupCanvas() {
  if (!canvasRef.value) return;

  renderer = new CanvasRenderer(canvasRef.value);
  redraw();
}

/**
 * Redraw the entire board
 */
function redraw() {
  if (!canvasRef.value || !renderer) return;

  const ctx = renderer.getContext();
  const cellSize = computedCellSize.value;
  const outside = props.outsideBorderThickness!;
  const inside = props.insideBorderThickness!;

  // Clear canvas
  renderer.clear();

  // Draw background
  // renderer.drawRect(0, 0, boardWidth.value, boardHeight.value, '#f0f0f0');

  // Draw top gutter cells
  if (props.gutterTop > 0) {
    const topGutterStartY = outside;
    for (let row = 0; row < props.gutterTop; row++) {
      for (let col = 0; col < props.cols; col++) {
        const x = gridStartX.value + col * (cellSize + inside);
        const y = topGutterStartY + row * (cellSize + inside);
        // Pass row as-is (0 to gutterTop-1) so renderer can detect it's in top gutter
        props.cellRenderer(ctx, row, col + props.gutterLeft, x, y, cellSize, props.state);
      }
    }
  }

  // Draw left gutter cells
  if (props.gutterLeft > 0) {
    const leftGutterStartX = outside;
    for (let row = 0; row < props.rows; row++) {
      for (let col = 0; col < props.gutterLeft; col++) {
        const x = leftGutterStartX + col * (cellSize + inside);
        const y = gridStartY.value + row * (cellSize + inside);
        // Pass col as-is (0 to gutterLeft-1) so renderer can detect it's in left gutter
        // Offset row by gutterTop so it doesn't conflict with top gutter rows
        props.cellRenderer(ctx, row + props.gutterTop, col, x, y, cellSize, props.state);
      }
    }
  }

  // Draw main grid cells
  for (let row = 0; row < props.rows; row++) {
    for (let col = 0; col < props.cols; col++) {
      const x = gridStartX.value + col * (cellSize + inside);
      const y = gridStartY.value + row * (cellSize + inside);

      // Offset row/col by gutter sizes so renderer knows these are main grid cells
      props.cellRenderer(ctx, row + props.gutterTop, col + props.gutterLeft, x, y, cellSize, props.state);
    }
  }

  // Draw right gutter cells
  if (props.gutterRight > 0) {
    const rightGutterStartX = gridStartX.value + props.cols * cellSize + Math.max(0, props.cols - 1) * inside + outside;
    for (let row = 0; row < props.rows; row++) {
      for (let col = 0; col < props.gutterRight; col++) {
        const x = rightGutterStartX + col * (cellSize + inside);
        const y = gridStartY.value + row * (cellSize + inside);
        props.cellRenderer(ctx, row + props.gutterTop, col + props.gutterLeft + props.cols, x, y, cellSize, props.state);
      }
    }
  }

  // Draw bottom gutter cells
  if (props.gutterBottom > 0) {
    const bottomGutterStartY = gridStartY.value + props.rows * cellSize + Math.max(0, props.rows - 1) * inside + outside;
    for (let row = 0; row < props.gutterBottom; row++) {
      for (let col = 0; col < props.cols; col++) {
        const x = gridStartX.value + col * (cellSize + inside);
        const y = bottomGutterStartY + row * (cellSize + inside);
        props.cellRenderer(ctx, row + props.gutterTop + props.rows, col + props.gutterLeft, x, y, cellSize, props.state);
      }
    }
  }

  // Draw grid lines
  if (props.drawGridLines) {
    drawGrid(ctx, cellSize);
  }
}

/**
 * Draw grid lines over the cells
 */
function drawGrid(ctx: CanvasRenderingContext2D, cellSize: number) {
  const outside = props.outsideBorderThickness!;
  const inside = props.insideBorderThickness!;

  const gridColor = props.gridColor || '#cccccc';
  const outsideBorderColor = props.outsideBorderColor || '#000000';

  // draw outside border
  ctx.strokeStyle = outsideBorderColor;
  ctx.lineWidth = outside;

  // Draw borders around actual content zones (not full perimeter to avoid corner areas)

  // Main grid border
  const mainGridX = gridStartX.value;
  const mainGridY = gridStartY.value;
  const mainGridWidth = props.cols * cellSize + Math.max(0, props.cols - 1) * inside;
  const mainGridHeight = props.rows * cellSize + Math.max(0, props.rows - 1) * inside;

  ctx.strokeRect(
    mainGridX - outside / 2,
    mainGridY - outside / 2,
    mainGridWidth + outside,
    mainGridHeight + outside
  );

  // Top gutter border (if exists and enabled)
  if (props.gutterTop > 0 && props.drawGutterTopOutsideBorder) {
    const topGutterX = mainGridX;
    const topGutterY = outside;
    const topGutterWidth = mainGridWidth;
    const topGutterHeight = props.gutterTop * cellSize + Math.max(0, props.gutterTop - 1) * inside;

    ctx.strokeRect(
      topGutterX - outside / 2,
      topGutterY - outside / 2,
      topGutterWidth + outside,
      topGutterHeight + outside
    );
  }

  // Left gutter border (if exists and enabled)
  if (props.gutterLeft > 0 && props.drawGutterLeftOutsideBorder) {
    const leftGutterX = outside;
    const leftGutterY = mainGridY;
    const leftGutterWidth = props.gutterLeft * cellSize + Math.max(0, props.gutterLeft - 1) * inside;
    const leftGutterHeight = mainGridHeight;

    ctx.strokeRect(
      leftGutterX - outside / 2,
      leftGutterY - outside / 2,
      leftGutterWidth + outside,
      leftGutterHeight + outside
    );
  }

  // Right gutter border (if exists and enabled)
  if (props.gutterRight > 0 && props.drawGutterRightOutsideBorder) {
    const rightGutterX = mainGridX + mainGridWidth + outside;
    const rightGutterY = mainGridY;
    const rightGutterWidth = props.gutterRight * cellSize + Math.max(0, props.gutterRight - 1) * inside;
    const rightGutterHeight = mainGridHeight;

    ctx.strokeRect(
      rightGutterX - outside / 2,
      rightGutterY - outside / 2,
      rightGutterWidth + outside,
      rightGutterHeight + outside
    );
  }

  // Bottom gutter border (if exists and enabled)
  if (props.gutterBottom > 0 && props.drawGutterBottomOutsideBorder) {
    const bottomGutterX = mainGridX;
    const bottomGutterY = mainGridY + mainGridHeight + outside;
    const bottomGutterWidth = mainGridWidth;
    const bottomGutterHeight = props.gutterBottom * cellSize + Math.max(0, props.gutterBottom - 1) * inside;

    ctx.strokeRect(
      bottomGutterX - outside / 2,
      bottomGutterY - outside / 2,
      bottomGutterWidth + outside,
      bottomGutterHeight + outside
    );
  }

  // draw inside borders
  ctx.strokeStyle = gridColor;
  ctx.lineWidth = inside;

  // Inside borders within main grid (horizontal)
  for (let i = 1; i < props.rows; i++) {
    const y = gridStartY.value + i * cellSize + (i - 1) * inside + inside / 2;
    ctx.beginPath();
    ctx.moveTo(gridStartX.value, y);
    ctx.lineTo(gridStartX.value + props.cols * cellSize + Math.max(0, props.cols - 1) * inside, y);
    ctx.stroke();
  }

  // Inside borders within main grid (vertical)
  for (let i = 1; i < props.cols; i++) {
    const x = gridStartX.value + i * cellSize + (i - 1) * inside + inside / 2;
    ctx.beginPath();
    ctx.moveTo(x, gridStartY.value);
    ctx.lineTo(x, gridStartY.value + props.rows * cellSize + Math.max(0, props.rows - 1) * inside);
    ctx.stroke();
  }

  // Inside borders within left gutter
  if (props.gutterLeft > 0) {
    const gutterStartX = outside;
    const drawHorizontal = props.gutterLeftInsideBorders === 'horizontal' || props.gutterLeftInsideBorders === 'both';
    const drawVertical = props.gutterLeftInsideBorders === 'vertical' || props.gutterLeftInsideBorders === 'both';

    // Horizontal borders in left gutter
    if (drawHorizontal) {
      for (let i = 1; i < props.rows; i++) {
        const y = gridStartY.value + i * cellSize + (i - 1) * inside + inside / 2;
        ctx.beginPath();
        ctx.moveTo(gutterStartX, y);
        ctx.lineTo(gutterStartX + props.gutterLeft * cellSize + Math.max(0, props.gutterLeft - 1) * inside, y);
        ctx.stroke();
      }
    }

    // Vertical borders in left gutter
    if (drawVertical && props.gutterLeft > 1) {
      for (let i = 1; i < props.gutterLeft; i++) {
        const x = gutterStartX + i * cellSize + (i - 1) * inside + inside / 2;
        ctx.beginPath();
        ctx.moveTo(x, gridStartY.value);
        ctx.lineTo(x, gridStartY.value + props.rows * cellSize + Math.max(0, props.rows - 1) * inside);
        ctx.stroke();
      }
    }
  }

  // Inside borders within top gutter
  if (props.gutterTop > 0) {
    const gutterStartY = outside;
    const drawHorizontal = props.gutterTopInsideBorders === 'horizontal' || props.gutterTopInsideBorders === 'both';
    const drawVertical = props.gutterTopInsideBorders === 'vertical' || props.gutterTopInsideBorders === 'both';

    // Horizontal borders in top gutter
    if (drawHorizontal && props.gutterTop > 1) {
      for (let i = 1; i < props.gutterTop; i++) {
        const y = gutterStartY + i * cellSize + (i - 1) * inside + inside / 2;
        ctx.beginPath();
        ctx.moveTo(gridStartX.value, y);
        ctx.lineTo(gridStartX.value + props.cols * cellSize + Math.max(0, props.cols - 1) * inside, y);
        ctx.stroke();
      }
    }

    // Vertical borders in top gutter
    if (drawVertical) {
      for (let i = 1; i < props.cols; i++) {
        const x = gridStartX.value + i * cellSize + (i - 1) * inside + inside / 2;
        ctx.beginPath();
        ctx.moveTo(x, gutterStartY);
        ctx.lineTo(x, gutterStartY + props.gutterTop * cellSize + Math.max(0, props.gutterTop - 1) * inside);
        ctx.stroke();
      }
    }
  }

  // === DRAW MAJOR GRID LINES (if configured) ===
  if (props.majorGridEvery !== undefined && props.majorGridEvery > 0) {
    const majorGridEvery = props.majorGridEvery;
    const majorGridColor = props.majorGridColor || '#808080';
    const majorGridThickness = props.majorGridThickness || 3;

    ctx.strokeStyle = majorGridColor;
    ctx.lineWidth = majorGridThickness;

    // Major horizontal lines
    for (let i = majorGridEvery; i < props.rows; i += majorGridEvery) {
      const y = gridStartY.value + i * cellSize + (i - 1) * inside + inside / 2;
      ctx.beginPath();
      ctx.moveTo(gridStartX.value, y);
      ctx.lineTo(gridStartX.value + props.cols * cellSize + Math.max(0, props.cols - 1) * inside, y);
      ctx.stroke();
    }

    // Major vertical lines
    for (let i = majorGridEvery; i < props.cols; i += majorGridEvery) {
      const x = gridStartX.value + i * cellSize + (i - 1) * inside + inside / 2;
      ctx.beginPath();
      ctx.moveTo(x, gridStartY.value);
      ctx.lineTo(x, gridStartY.value + props.rows * cellSize + Math.max(0, props.rows - 1) * inside);
      ctx.stroke();
    }
  }
}

/**
 * Convert canvas coordinates to cell row/col
 * Supports both game grid and gutter regions
 */
function getCellFromCoords(x: number, y: number): CellCoordinate | null {
  const cellSize = computedCellSize.value;
  const outside = props.outsideBorderThickness!;
  const inside = props.insideBorderThickness!;

  // Check top gutter
  if (props.gutterTop > 0) {
    const topGutterStartY = outside;
    const topGutterEndY = topGutterStartY + props.gutterTop * cellSize + Math.max(0, props.gutterTop - 1) * inside;

    if (y >= topGutterStartY && y < topGutterEndY) {
      const adjustedX = x - gridStartX.value;
      const adjustedY = y - topGutterStartY;

      const col = Math.floor(adjustedX / (cellSize + inside));
      const row = Math.floor(adjustedY / (cellSize + inside));

      if (row >= 0 && row < props.gutterTop && col >= 0 && col < props.cols) {
        const cellX = gridStartX.value + col * (cellSize + inside);
        const cellY = topGutterStartY + row * (cellSize + inside);

        if (x >= cellX && x < cellX + cellSize && y >= cellY && y < cellY + cellSize) {
          return { row, col, zone: 'topGutter' };
        }
      }
    }
  }

  // Check left gutter
  if (props.gutterLeft > 0) {
    const leftGutterStartX = outside;
    const leftGutterEndX = leftGutterStartX + props.gutterLeft * cellSize + Math.max(0, props.gutterLeft - 1) * inside;

    if (x >= leftGutterStartX && x < leftGutterEndX) {
      const adjustedX = x - leftGutterStartX;
      const adjustedY = y - gridStartY.value;

      const col = Math.floor(adjustedX / (cellSize + inside));
      const row = Math.floor(adjustedY / (cellSize + inside));

      if (row >= 0 && row < props.rows && col >= 0 && col < props.gutterLeft) {
        const cellX = leftGutterStartX + col * (cellSize + inside);
        const cellY = gridStartY.value + row * (cellSize + inside);

        if (x >= cellX && x < cellX + cellSize && y >= cellY && y < cellY + cellSize) {
          return { row, col, zone: 'leftGutter' };
        }
      }
    }
  }

  // Check right gutter
  if (props.gutterRight > 0) {
    const rightGutterStartX = gridStartX.value + props.cols * cellSize + Math.max(0, props.cols - 1) * inside + outside;

    if (x >= rightGutterStartX) {
      const adjustedX = x - rightGutterStartX;
      const adjustedY = y - gridStartY.value;

      const col = Math.floor(adjustedX / (cellSize + inside));
      const row = Math.floor(adjustedY / (cellSize + inside));

      if (row >= 0 && row < props.rows && col >= 0 && col < props.gutterRight) {
        const cellX = rightGutterStartX + col * (cellSize + inside);
        const cellY = gridStartY.value + row * (cellSize + inside);

        if (x >= cellX && x < cellX + cellSize && y >= cellY && y < cellY + cellSize) {
          return { row, col, zone: 'rightGutter' };
        }
      }
    }
  }

  // Check bottom gutter
  if (props.gutterBottom > 0) {
    const bottomGutterStartY = gridStartY.value + props.rows * cellSize + Math.max(0, props.rows - 1) * inside + outside;

    if (y >= bottomGutterStartY) {
      const adjustedX = x - gridStartX.value;
      const adjustedY = y - bottomGutterStartY;

      const col = Math.floor(adjustedX / (cellSize + inside));
      const row = Math.floor(adjustedY / (cellSize + inside));

      if (row >= 0 && row < props.gutterBottom && col >= 0 && col < props.cols) {
        const cellX = gridStartX.value + col * (cellSize + inside);
        const cellY = bottomGutterStartY + row * (cellSize + inside);

        if (x >= cellX && x < cellX + cellSize && y >= cellY && y < cellY + cellSize) {
          return { row, col, zone: 'bottomGutter' };
        }
      }
    }
  }

  // Check main game grid
  const adjustedX = x - gridStartX.value;
  const adjustedY = y - gridStartY.value;

  const col = Math.floor(adjustedX / (cellSize + inside));
  const row = Math.floor(adjustedY / (cellSize + inside));

  if (row >= 0 && row < props.rows && col >= 0 && col < props.cols) {
    const cellX = gridStartX.value + col * (cellSize + inside);
    const cellY = gridStartY.value + row * (cellSize + inside);

    if (x >= cellX && x < cellX + cellSize && y >= cellY && y < cellY + cellSize) {
      return { row, col, zone: 'game' };
    }
  }

  return null;
}

/**
 * Helper to get cell coordinates from mouse event
 */
function getCellFromEvent(event: MouseEvent): CellCoordinate | null {
  if (!canvasRef.value) return null;

  const rect = canvasRef.value.getBoundingClientRect();
  const x = event.clientX - rect.left;
  const y = event.clientY - rect.top;

  return getCellFromCoords(x, y);
}

/**
 * Event Handlers - emit Vue events directly
 */
function handle_mousedown(event: MouseEvent) {
  const cell = getCellFromEvent(event);
  if (!cell) return;

  last_mousedown_cell = cell;
  emit('cell-mousedown', cell, event);
}

function handle_mouseup(event: MouseEvent) {
  const cell = getCellFromEvent(event);
  if (!cell) return;

  emit('cell-mouseup', cell, event);

  // Detect click (mousedown and mouseup on same cell)
  if (
    last_mousedown_cell &&
    last_mousedown_cell.row === cell.row &&
    last_mousedown_cell.col === cell.col &&
    last_mousedown_cell.zone === cell.zone
  ) {
    emit('cell-click', cell);

    // Update focus if cell changed
    if (
      !focused_cell ||
      focused_cell.row !== cell.row ||
      focused_cell.col !== cell.col
    ) {
      emit('cell-focus', cell, event);
      focused_cell = cell;
    }
  }

  last_mousedown_cell = null;
}

function handle_mousemove(event: MouseEvent) {
  const cell = getCellFromEvent(event);

  if (cell) {
    // Cell enter/leave tracking
    if (
      !last_hover_cell ||
      last_hover_cell.row !== cell.row ||
      last_hover_cell.col !== cell.col
    ) {
      if (last_hover_cell) {
        emit('cell-leave', last_hover_cell, event);
      }
      emit('cell-enter', cell, event);
      last_hover_cell = cell;
    }
  } else if (last_hover_cell) {
    emit('cell-leave', last_hover_cell, event);
    last_hover_cell = null;
  }
}

function handle_board_enter(event: MouseEvent) {
  emit('board-enter', event);
}

function handle_board_leave(event: MouseEvent) {
  if (last_hover_cell) {
    emit('cell-leave', last_hover_cell, event);
    last_hover_cell = null;
  }
  emit('board-leave', event);
}

function handle_keydown(event: KeyboardEvent) {
  // Only handle if a cell is focused
  if (!focused_cell) return;

  // Emit as cell-keydown (add to emit types if needed)
  // For now, games can handle keyboard via their own listeners
}

let lastScale = window.visualViewport?.scale || 1;

/** Handle window resize and zoom events */
function handleWindowResize() {
  if (renderer && canvasRef.value) {
    renderer.setupHighDPI();
    redraw();
  }
}

function handleViewportChange() {
  const currentScale = window.visualViewport?.scale || 1;

  if (currentScale !== lastScale) {
    lastScale = currentScale;
    handleWindowResize();
  }
}

onMounted(async () => {
  // Wait for DOM to fully render
  await nextTick();

  // Wait for browser to complete layout and paint
  await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));

  // Set up ResizeObserver first - it will trigger proper sizing when layout settles
  if (containerRef.value) {
    containerResizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const new_width = entry.contentRect.width;
        const new_height = entry.contentRect.height;

        // Only update if we have a valid size and it changed
        if (new_width > 0 && new_height > 0 &&
            (containerSize.value.width !== new_width || containerSize.value.height !== new_height)) {
          containerSize.value = {
            width: new_width,
            height: new_height
          };
        }
      }
    });
    containerResizeObserver.observe(containerRef.value);

    // Read initial size - ResizeObserver will also fire immediately
    const initialWidth = containerRef.value.clientWidth;
    const initialHeight = containerRef.value.clientHeight;
    if (initialWidth > 0 && initialHeight > 0) {
      containerSize.value = {
        width: initialWidth,
        height: initialHeight
      };
    }
  }
  setupCanvas();

  window.addEventListener('resize', handleWindowResize);

  if (window.visualViewport) {
    window.visualViewport.addEventListener('resize', handleViewportChange);
    window.visualViewport.addEventListener('scroll', handleViewportChange);
  }
});

onBeforeUnmount(() => {
  if (containerResizeObserver) {
    containerResizeObserver.disconnect();
    containerResizeObserver = null;
  }

  window.removeEventListener('resize', handleWindowResize);

  if (window.visualViewport) {
    window.visualViewport.removeEventListener('resize', handleViewportChange);
    window.visualViewport.removeEventListener('scroll', handleViewportChange);
  }
});

// Watch for changes and redraw
watch(
  () => [props.state.board, props.rows, props.cols, computedCellSize.value, props.scale, props.cellRenderer],
  () => {
    redraw();
  },
  { deep: true }
);

// Watch container size changes to trigger initial render and handle resize
watch(
  containerSize,
  () => {
    if (renderer && canvasRef.value) {
      // Use double RAF to ensure browser has completed layout before redrawing
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          renderer?.setupHighDPI();
          redraw();

          // Safety net: redraw again after a short delay in case layout wasn't fully settled
          setTimeout(() => {
            if (renderer && canvasRef.value) {
              renderer.setupHighDPI();
              redraw();
            }
          }, 50);
        });
      });
    }
  },
  { deep: true }
);


// Export canvas as PNG (dev utility)
function exportAsPng(filename?: string) {
  if (!canvasRef.value) return;

  const link = document.createElement('a');
  link.download = filename || 'board.png';
  link.href = canvasRef.value.toDataURL('image/png');
  link.click();
}

// Expose methods for parent components
defineExpose({
  redraw,
  getCellFromCoords,
  getCanvas: () => canvasRef.value,
  exportAsPng
});
</script>

<template>
  <div ref="containerRef" class="w-full h-full flex items-center justify-center">
    <div class="w-full h-full flex items-center justify-center">
      <canvas
        ref="canvasRef"
        :width="boardWidth"
        :height="boardHeight"
        tabindex="0"
        @contextmenu.prevent
        @mousedown="handle_mousedown"
        @mouseup="handle_mouseup"
        @mousemove="handle_mousemove"
        @mouseenter="handle_board_enter"
        @mouseleave="handle_board_leave"
        @keydown="handle_keydown"
        @dblclick="props.enableExport && exportAsPng()"
        @dragstart.prevent
        class="block !w-full !h-full object-contain [touch-action:manipulation] [image-rendering:pixelated]"
      />
    </div>
  </div>
</template>
