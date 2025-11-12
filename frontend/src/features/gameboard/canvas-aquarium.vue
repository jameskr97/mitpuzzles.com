<script setup lang="ts">
/**
 * canvas-aquarium - Canvas-based renderer for Aquarium (home page preview)
 *
 * Renders a grid with region borders and row/column hints. Used for static display.
 */
import { computed, ref, onMounted } from "vue";
import CanvasBoard from "./canvas-board.vue";
import { useCanvasTheme } from "./canvas-theme";
import type { CellRenderer } from "./canvas-types";
import { draw_region_borders } from "./canvas-utils";
import type { PuzzleState } from "@/services/game/engines/types";

const props = defineProps<{
  state: PuzzleState;
}>();

const { theme } = useCanvasTheme();

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
});

// Aquarium cell values
const AquariumCell = {
  EMPTY: -1,
  WATER: -3,
  CROSS: -4,
} as const;

// Constants for rendering
const REGION_BORDER_WIDTH = 3;
const CELL_BORDER_WIDTH = 1;

const cell_renderer = computed((): CellRenderer => {
  const _ = image_loaded.value; // Access for reactivity
  const current_theme = theme.value;
  const current_cross = cross_image.value;
  const rows = props.state.definition.rows;
  const cols = props.state.definition.cols;
  const meta = props.state.definition.meta as { regions?: number[][]; row_hints?: number[]; col_hints?: number[] } | undefined;

  return (ctx, row, col, x, y, size, _state) => {
    // Helper function to set up text rendering
    const setup_gutter_text = (color: string) => {
      ctx.fillStyle = color;
      ctx.font = `bold ${size * 0.6}px Roboto, sans-serif`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
    };

    // Top gutter: column hints
    if (row === 0 && col >= 1) {
      const board_col = col - 1;
      const col_hint = meta?.col_hints?.[board_col] ?? 0;
      setup_gutter_text("#000000");
      ctx.fillText(col_hint.toString(), x + size / 2, y + size / 2 + 2);
      return;
    }

    // Left gutter: row hints
    if (col === 0 && row >= 1) {
      const board_row = row - 1;
      const row_hint = meta?.row_hints?.[board_row] ?? 0;
      setup_gutter_text("#000000");
      ctx.fillText(row_hint.toString(), x + size / 2, y + size / 2 + 2);
      return;
    }

    // Corner cell (top-left)
    if (row === 0 && col === 0) {
      return;
    }

    // Main grid: adjust indices for board access (subtract gutters)
    const board_row = row - 1;
    const board_col = col - 1;

    // Bounds check
    if (board_row < 0 || board_row >= rows || board_col < 0 || board_col >= cols) {
      return;
    }

    const value = props.state.board[board_row]?.[board_col] ?? AquariumCell.EMPTY;
    const region_map = meta?.regions || [];

    // Determine cell background color
    let bg_color: string;
    if (value === AquariumCell.WATER) {
      bg_color = "#60a5fa"; // Blue for water
    } else {
      bg_color = "#ffffff"; // White for empty/cross
    }

    // Draw cell background
    ctx.fillStyle = bg_color;
    ctx.fillRect(x, y, size, size);

    // Draw X mark for CROSS cells (using Kakurasu cross image)
    if (value === AquariumCell.CROSS) {
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

    // Draw thin cell border
    ctx.strokeStyle = "#d1d5db";
    ctx.lineWidth = CELL_BORDER_WIDTH;
    ctx.strokeRect(x, y, size, size);

    // Draw thick region borders
    if (region_map.length > 0) {
      draw_region_borders(ctx, board_row, board_col, x, y, size, rows, cols, region_map, {
        border_width: REGION_BORDER_WIDTH,
      });
    }
  };
});
</script>

<template>
  <CanvasBoard
    :rows="state.definition.rows"
    :cols="state.definition.cols"
    :state="state"
    :cell-renderer="cell_renderer"
    :gap="0"
    :gutter-top="1"
    :gutter-left="1"
    :gutter-top-inside-borders="'none'"
    :gutter-left-inside-borders="'none'"
    :draw-gutter-top-outside-border="false"
    :draw-gutter-left-outside-border="false"
    grid-color="transparent"
    outside-border-color="#000000"
    :inside-border-thickness="0"
    :outside-border-thickness="3"
  />
</template>
