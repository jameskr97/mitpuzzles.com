<script setup lang="ts">
/**
 * KakurasuCanvas - Canvas-based renderer for Kakurasu
 *
 * Clean event-based interface - emits cell-click events.
 * No dependency on old interaction bridge.
 */
import { ref, computed, onMounted, onUnmounted } from "vue";
import CanvasBoard from "@/features/gameboard/canvas-board.vue";
import { useCanvasTheme } from "@/features/gameboard/canvas-theme";
import type { CellRenderer } from "@/features/gameboard/canvas-types";
import { KakurasuCell } from "./useKakurasuGame";
import type { KakurasuMeta, RuleViolation } from "@/core/games/types/puzzle-types.ts";

// Props
const props = defineProps<{
  state: {
    definition: {
      rows: number;
      cols: number;
      meta: KakurasuMeta;
    };
    board: number[][];
    violations?: RuleViolation[];
  };
}>();

// Events
const emit = defineEmits<{
  (e: "cell-click", row: number, col: number, button: number): void;
  (e: "cell-drag", row: number, col: number): void;
  (e: "cell-enter", row: number, col: number, zone: string): void;
  (e: "cell-leave", row: number, col: number, zone: string): void;
}>();

// Track hovered cell for hover event recording
const hovered_cell = ref<{ row: number; col: number; zone: string } | null>(null);

// Theme support
const { theme } = useCanvasTheme();

// Canvas board ref
const canvas_board_ref = ref<InstanceType<typeof CanvasBoard> | null>(null);

// Drag state for click-and-drag support
const is_dragging = ref(false);
const drag_button = ref<number>(0);
const dragged_cells = ref<Set<string>>(new Set());

// Preload cross image
const cross_image = ref<HTMLImageElement | null>(null);
const image_loaded = ref(false);

onMounted(() => {
  const img = new Image();
  img.src = "/assets/kakurasu/cross.svg";
  img.onload = () => {
    cross_image.value = img;
    image_loaded.value = true;
  };

  // Document-level mouseup listener for drag
  document.addEventListener("mouseup", stop_drag);
});

onUnmounted(() => {
  document.removeEventListener("mouseup", stop_drag);
});

// Handle cell mousedown - start drag and emit first click
function on_cell_mousedown(coord: { row: number; col: number; zone: string }, event: MouseEvent) {
  if (coord.zone !== "game") return;

  // Start drag tracking
  is_dragging.value = true;
  drag_button.value = event.button;
  dragged_cells.value = new Set([`${coord.row},${coord.col}`]);

  emit("cell-click", coord.row, coord.col, event.button);
}

// Handle cell enter during drag - emit drag event for new cells
function on_cell_enter(coord: { row: number; col: number; zone: string }, _event: MouseEvent) {
  // Emit hover enter for tracking (all zones)
  hovered_cell.value = { row: coord.row, col: coord.col, zone: coord.zone };
  emit("cell-enter", coord.row, coord.col, coord.zone);

  // Handle drag (game zone only)
  if (coord.zone !== "game" || !is_dragging.value) return;
  const cell_key = `${coord.row},${coord.col}`;
  if (dragged_cells.value.has(cell_key)) return;
  dragged_cells.value.add(cell_key);
  emit("cell-drag", coord.row, coord.col);
}

function on_cell_leave(coord: { row: number; col: number; zone: string }, _event: MouseEvent) {
  emit("cell-leave", coord.row, coord.col, coord.zone);
}

function on_board_leave(_event: MouseEvent) {
  if (hovered_cell.value) {
    emit("cell-leave", hovered_cell.value.row, hovered_cell.value.col, hovered_cell.value.zone);
  }
  hovered_cell.value = null;
}

// Handle mouseup anywhere - stop drag
function stop_drag() {
  is_dragging.value = false;
  dragged_cells.value.clear();
}

// Kakurasu cell renderer
const cell_renderer = computed((): CellRenderer => {
  // Access for reactivity
  const _ = image_loaded.value;
  const current_theme = theme.value;
  const current_cross = cross_image.value;

  return (ctx, row, col, x, y, size, state) => {
    const puzzle_state = props.state;

    // Helper function to set up text rendering
    const setup_gutter_text = (color: string) => {
      ctx.fillStyle = color;
      ctx.font = `${size * 0.7}px Roboto, sans-serif`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
    };

    // Top gutter: column numbers (1, 2, 3...)
    if (row === 0) {
      setup_gutter_text(current_theme.hint);
      ctx.fillText(col.toString(), x + size / 2, y + size / 2 + 3);
      return;
    }

    // Left gutter: row numbers (1, 2, 3...)
    if (col === 0) {
      setup_gutter_text(current_theme.hint);
      ctx.fillText(row.toString(), x + size / 2, y + size / 2 + 3);
      return;
    }

    // Right gutter: row sums with violation highlighting
    if (col === 1 + puzzle_state.definition.cols) {
      const board_row = row - 1;
      const row_sum = puzzle_state.definition.meta.row_sums[board_row];
      const has_violation = puzzle_state.violations?.some(
        (v) =>
          v.rule_name === "line_sum_row_exceeded" &&
          v.locations?.some((loc) => loc.row === board_row && loc.col === -1)
      );
      setup_gutter_text(has_violation ? current_theme.error : current_theme.blue);
      ctx.fillText(row_sum.toString(), x + size / 2, y + size / 2 + 3);
      return;
    }

    // Bottom gutter: column sums with violation highlighting
    if (row === 1 + puzzle_state.definition.rows) {
      const board_col = col - 1;
      const col_sum = puzzle_state.definition.meta.col_sums[board_col];
      const has_violation = puzzle_state.violations?.some(
        (v) =>
          v.rule_name === "line_sum_col_exceeded" &&
          v.locations?.some((loc) => loc.col === board_col && loc.row === -1)
      );
      setup_gutter_text(has_violation ? current_theme.error : current_theme.blue);
      ctx.fillText(col_sum.toString(), x + size / 2, y + size / 2 + 3);
      return;
    }

    // Main grid: adjust indices for board access (subtract gutters)
    const board_row = row - 1;
    const board_col = col - 1;
    const value = puzzle_state.board[board_row][board_col];

    // Draw cell background
    ctx.fillStyle = current_theme.background;
    ctx.fillRect(x, y, size, size);

    // Render cell content based on type
    if (value === KakurasuCell.BLACK) {
      // Black filled cell with white border
      ctx.fillStyle = current_theme.wall;
      const outline_width = 2;
      const ow2 = outline_width * 2;
      ctx.fillRect(x + outline_width, y + outline_width, size - ow2, size - ow2);
    } else if (value === KakurasuCell.CROSS) {
      // Cross mark
      if (current_cross) {
        const img_size = size * 0.67;
        const offset = (size - img_size) / 2;
        ctx.drawImage(current_cross, x + offset, y + offset, img_size, img_size);
      } else {
        // Fallback: draw X with lines
        ctx.strokeStyle = current_theme.text;
        ctx.lineWidth = 2;
        const padding = size * 0.17;
        ctx.beginPath();
        ctx.moveTo(x + padding, y + padding);
        ctx.lineTo(x + size - padding, y + size - padding);
        ctx.moveTo(x + size - padding, y + padding);
        ctx.lineTo(x + padding, y + size - padding);
        ctx.stroke();
      }
    }
  };
});
</script>

<template>
  <CanvasBoard
    ref="canvas_board_ref"
    :rows="state.definition.rows"
    :cols="state.definition.cols"
    :state="state"
    :cell-renderer="cell_renderer"
    :gap="1"
    :gutter-top="1"
    :gutter-left="1"
    :gutter-right="1"
    :gutter-bottom="1"
    :gutter-top-inside-borders="'none'"
    :gutter-left-inside-borders="'none'"
    :gutter-right-inside-borders="'none'"
    :gutter-bottom-inside-borders="'none'"
    :draw-gutter-top-outside-border="false"
    :draw-gutter-left-outside-border="false"
    :draw-gutter-right-outside-border="false"
    :draw-gutter-bottom-outside-border="false"
    :outside-border-thickness="2"
    @cell-mousedown="on_cell_mousedown"
    @cell-enter="on_cell_enter"
    @cell-leave="on_cell_leave"
    @board-leave="on_board_leave"
  />
</template>
