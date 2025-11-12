<script setup lang="ts">
/**
 * canvas-norinori - Canvas-based renderer for Norinori (home page preview)
 *
 * Renders a grid with region borders. Used for static display.
 */
import { computed } from "vue";
import CanvasBoard from "./canvas-board.vue";
import { useCanvasTheme } from "./canvas-theme";
import type { CellRenderer } from "./canvas-types";
import { draw_region_borders } from "./canvas-utils";
import type { PuzzleState } from "@/services/game/engines/types";

const props = defineProps<{
  state: PuzzleState;
}>();

const { theme } = useCanvasTheme();

// Norinori cell values
const NorinoriCell = {
  EMPTY: -1,
  SHADED: -3,
  CROSS: -4,
} as const;

// Constants for rendering
const REGION_BORDER_WIDTH = 3;
const CELL_BORDER_WIDTH = 1;

const cell_renderer = computed((): CellRenderer => {
  const current_theme = theme.value;
  const rows = props.state.definition.rows;
  const cols = props.state.definition.cols;
  const region_map = props.state.definition.meta?.regions || [];

  return (ctx, row, col, x, y, size, _state) => {
    const value = props.state.board[row]?.[col] ?? NorinoriCell.EMPTY;

    // Determine cell background color
    let bg_color: string;
    if (value === NorinoriCell.SHADED) {
      bg_color = "#6b7280"; // Medium gray for shaded
    } else {
      bg_color = "#ffffff"; // White for empty/cross
    }

    // Draw cell background
    ctx.fillStyle = bg_color;
    ctx.fillRect(x, y, size, size);

    // Draw X mark for CROSS cells
    if (value === NorinoriCell.CROSS) {
      ctx.strokeStyle = "#9ca3af";
      ctx.lineWidth = 2;
      const padding = size * 0.25;
      ctx.beginPath();
      ctx.moveTo(x + padding, y + padding);
      ctx.lineTo(x + size - padding, y + size - padding);
      ctx.moveTo(x + size - padding, y + padding);
      ctx.lineTo(x + padding, y + size - padding);
      ctx.stroke();
    }

    // Draw thin cell border
    ctx.strokeStyle = "#d1d5db";
    ctx.lineWidth = CELL_BORDER_WIDTH;
    ctx.strokeRect(x, y, size, size);

    // Draw thick region borders
    draw_region_borders(ctx, row, col, x, y, size, rows, cols, region_map, {
      border_width: REGION_BORDER_WIDTH,
    });
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
    grid-color="transparent"
    outside-border-color="#000000"
    :inside-border-thickness="0"
    :outside-border-thickness="3"
  />
</template>
