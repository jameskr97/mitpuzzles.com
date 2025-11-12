<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import CanvasBoard from "./canvas-board.vue";
import { useCanvasTheme } from "./canvas-theme";
import type { PuzzleState, KakurasuMeta } from "@/services/game/engines/types";
import type { createPuzzleInteractionBridge } from "@/features/games.composables/setupPuzzleInteractionBridge";
import type { CellRenderer } from "./canvas-types";
import { KakurasuCell } from "@/services/game/engines/translator";

// Props
const props = defineProps<{
  state: PuzzleState<KakurasuMeta>;
  interact?: ReturnType<typeof createPuzzleInteractionBridge>;
}>();

// Theme support
const { theme } = useCanvasTheme();

// Preload cross image
const cross_image = ref<HTMLImageElement | null>(null);

onMounted(() => {
  const img = new Image();
  img.src = "/assets/kakurasu/cross.svg";
  img.onload = () => {
    cross_image.value = img;
  };
});

// Kakurasu cell renderer
const cell_renderer = computed((): CellRenderer => {
  const current_theme = theme.value;
  const current_cross = cross_image.value;

  return (ctx, row, col, x, y, size, state) => {
    const puzzle_state = state as PuzzleState<KakurasuMeta>;

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
      ctx.fillText(col.toString(), x + size / 2, (y + size / 2) + 3);
      return;
    }

    // Left gutter: row numbers (1, 2, 3...)
    if (col === 0) {
      setup_gutter_text(current_theme.hint);
      ctx.fillText(row.toString(), x + size / 2, (y + size / 2) + 3);
      return;
    }

    // Right gutter: row sums with violation highlighting
    if (col === 1 + puzzle_state.definition.cols) {
      const board_row = row - 1; // Subtract gutterTop
      const row_sum = puzzle_state.definition.meta!.row_sums[board_row];
      const has_violation = puzzle_state.violations?.some(
        (v) => v.rule_name === "line_sum_row_exceeded" && v.locations?.some((loc) => loc.row === board_row && loc.col === -1),
      );
      setup_gutter_text(has_violation ? current_theme.error : current_theme.blue);
      ctx.fillText(row_sum.toString(), x + size / 2, (y + size / 2) + 3);
      return;
    }

    // Bottom gutter: column sums with violation highlighting
    if (row === 1 + puzzle_state.definition.rows) {
      const board_col = col - 1; // Subtract gutterLeft
      const col_sum = puzzle_state.definition.meta!.col_sums[board_col];
      const has_violation = puzzle_state.violations?.some(
        (v) => v.rule_name === "line_sum_col_exceeded" && v.locations?.some((loc) => loc.col === board_col && loc.row === -1),
      );
      setup_gutter_text(has_violation ? current_theme.error : current_theme.blue);
      ctx.fillText(col_sum.toString(), x + size / 2, (y + size / 2) + 3);
      return;
    }

    // Main grid: adjust indices for board access (subtract gutters)
    const board_row = row - 1; // Subtract gutterTop
    const board_col = col - 1; // Subtract gutterLeft
    const value = puzzle_state.board[board_row][board_col];

    // Draw cell background
    ctx.fillStyle = current_theme.background;
    ctx.fillRect(x, y, size, size);

    // Render cell content based on type
    if (value === KakurasuCell.BLACK) {
      // Black filled cell with white border
      ctx.fillStyle = current_theme.wall;
      let outline_width = 2;
      let ow2 = outline_width * 2;
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
    :rows="state.definition.rows"
    :cols="state.definition.cols"
    :state="state"
    :interact="interact"
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
  />
</template>
