<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import CanvasBoard from "./canvas-board.vue";
import { useCanvasTheme } from "./canvas-theme";
import type { PuzzleState, TentsMeta } from "@/services/game/engines/types";
import type { createPuzzleInteractionBridge } from "@/features/games.composables/setupPuzzleInteractionBridge";
import type { CellRenderer } from "./canvas-types";
import { TentsCell } from "@/services/game/engines/translator";

// Props
const props = defineProps<{
  state: PuzzleState<TentsMeta>;
  interact?: ReturnType<typeof createPuzzleInteractionBridge>;
}>();

const { theme } = useCanvasTheme();

// Preload images
const images = ref<Record<string, HTMLImageElement | null>>({
  tent: null,
  tree: null,
});

// Track when images are loaded to trigger re-render
const images_loaded = ref(0);

onMounted(() => {
  const assets = {
    tent: "/assets/tents/tent.svg",
    tree: "/assets/tents/tree.svg",
  };

  for (const [key, path] of Object.entries(assets)) {
    const img = new Image();
    img.src = path;
    img.onload = () => {
      images.value[key] = img;
      images_loaded.value++;
    };
  }
});

// Tents cell renderer
const cell_renderer = computed((): CellRenderer => {
  // Access images_loaded to create reactive dependency
  const _ = images_loaded.value;
  const current_theme = theme.value;
  const current_images = images.value;

  return (ctx, row, col, x, y, size, state) => {
    const puzzle_state = state as PuzzleState<TentsMeta>;

    // Top gutter: column tent counts (row 0, col is offset by gutterLeft)
    if (row === 0) {
      const actual_col = col - 1; // Subtract gutterLeft (which is 1)
      const col_count = puzzle_state.definition.meta!.col_tent_counts[actual_col];
      const has_col_violation = puzzle_state.violations?.some(
        (v) =>
          v.rule_name === "line_sum_col_exceeded" &&
          v.locations?.some((loc) => loc.row === -1 && loc.col === actual_col),
      );

      ctx.fillStyle = has_col_violation ? current_theme.error : 'black';
      ctx.font = `bold ${size * 0.7}px sans-serif`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(col_count.toString(), x + size / 2, y + size / 2);
      return;
    }

    // Left gutter: row tent counts (col 0, row is offset by gutterTop)
    if (col === 0) {
      const actual_row = row - 1; // Subtract gutterTop (which is 1)
      const row_count = puzzle_state.definition.meta!.row_tent_counts[actual_row];
      const has_row_violation = puzzle_state.violations?.some(
        (v) =>
          v.rule_name === "line_sum_row_exceeded" &&
          v.locations?.some((loc) => loc.row === actual_row && loc.col === -1),
      );

      ctx.fillStyle = has_row_violation ? current_theme.error : 'black';
      ctx.font = `bold ${size * 0.7}px sans-serif`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(row_count.toString(), x + size / 2, y + size / 2);
      return;
    }

    // Main grid: adjust indices for board access (subtract gutters)
    const board_row = row - 1; // Subtract gutterTop
    const board_col = col - 1; // Subtract gutterLeft
    const value = puzzle_state.board[board_row][board_col];

    // Check for tent intersection violation
    const has_violation = puzzle_state.violations?.some(
      (v) =>
        v.rule_name === "tents_intersecting" &&
        v.locations?.some((loc) => loc.row === board_row && loc.col === board_col),
    );

    // Determine background color
    const green_bg = "#7bf1a8"; // green-300
    const red_bg = "#fca5a5"; // red-300

    // Draw based on cell type
    if (value === TentsCell.TENT) {
      // Tent: green or red background + tent image
      ctx.fillStyle = has_violation ? red_bg : green_bg;
      ctx.fillRect(x, y, size + 1, size + 1);

      if (current_images.tent) {
        ctx.drawImage(current_images.tent, x, y, size, size);
      }
    } else if (value === TentsCell.TREE) {
      // Tree: green background + tree image
      ctx.fillStyle = green_bg;
      ctx.fillRect(x, y, size + 1, size + 1);

      if (current_images.tree) {
        ctx.drawImage(current_images.tree, x, y, size, size);
      }
    } else if (value === TentsCell.GREEN) {
      // Green: just green background
      ctx.fillStyle = green_bg;
      ctx.fillRect(x, y, size + 1, size + 1);
    }
    // EMPTY: no rendering (default background)
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
    :gutter-top="1"
    :gutter-left="1"
    :gutter-top-inside-borders="'none'"
    :gutter-left-inside-borders="'none'"
    :draw-gutter-top-outside-border="false"
    :draw-gutter-left-outside-border="false"
    :outside-border-thickness="2"
    :inside-border-thickness="2"
  />
</template>
