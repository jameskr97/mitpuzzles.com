<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import CanvasBoard from "./canvas-board.vue";
import { useCanvasTheme } from "./canvas-theme";
import { useGutterMarking } from "@/features/games.composables/useGutterMarking";
import type { PuzzleState, NonogramMeta } from "@/services/game/engines/types";
import type { createPuzzleInteractionBridge } from "@/features/games.composables/setupPuzzleInteractionBridge";
import type { CellRenderer } from "./canvas-types";
import { KakurasuCell } from "@/services/game/engines/translator";

// Props
const props = defineProps<{
  state: PuzzleState<NonogramMeta>;
  interact?: ReturnType<typeof createPuzzleInteractionBridge>;
}>();
props.interact?.addDefaultBehaviors();

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

// Calculate gutter sizes based on longest hint arrays
const longest_array = (array: Array<Array<number>>) =>
  array.reduce((longest, current) => {
    return current.length > longest.length ? current : longest;
  }, []);

const gutter_left = computed(() =>
  longest_array(props.state.definition.meta!.row_hints).length ?? 0
);

const gutter_top = computed(() =>
  longest_array(props.state.definition.meta!.col_hints).length ?? 0
);

// Calculate gutter sizes for marking
const gutter_sizes = computed(() => ({
  top: gutter_top.value * props.state.definition.cols,
  left: gutter_left.value * props.state.definition.rows
}));

// Initialize gutter marking
const { is_marked, current_markings } = useGutterMarking('nonograms', gutter_sizes.value);

// Index calculation for gutter marking (matches useNonogramGutterMarking.ts)
const get_top_gutter_index = (row: number, col: number): number =>
  row * props.state.definition.cols + col;

const get_left_gutter_index = (row: number, col: number): number =>
  col * props.state.definition.rows + row;

// Nonograms cell renderer
const cell_renderer = computed((): CellRenderer => {
  const current_theme = theme.value;
  const current_cross = cross_image.value;
  // Access current_markings to establish reactive dependency
  const markings = current_markings.value;

  return (ctx, row, col, x, y, size, state) => {
    const puzzle_state = state as PuzzleState<NonogramMeta>;

    // Top gutter: column hints
    if (row < gutter_top.value) {
      // Draw white background
      ctx.fillStyle = current_theme.background;
      ctx.fillRect(x, y, size + 1, size + 1);

      // col is offset by gutter_left, so subtract it to get actual column index
      const actual_col = col - gutter_left.value;
      const col_hints = puzzle_state.definition.meta!.col_hints[actual_col];
      const hint_index = row - (gutter_top.value - col_hints.length);

      if (hint_index >= 0 && hint_index < col_hints.length) {
        const hint = col_hints[hint_index];

        // Check if this gutter cell is marked
        const gutter_index = get_top_gutter_index(row, actual_col);
        const marked = is_marked('top', gutter_index);

        ctx.fillStyle = marked ? "#d1d5db" : "#9ca3af"; // gray-300 if marked, gray-400 if not
        ctx.font = `${size * 0.6}px sans-serif`;
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(hint.toString(), x + size / 2, y + size / 2);
      }
      return;
    }

    // Left gutter: row hints
    if (col < gutter_left.value) {
      // Draw white background
      ctx.fillStyle = current_theme.background;
      ctx.fillRect(x, y, size + 1, size + 1);

      // row is offset by gutter_top, so subtract it to get actual row index
      const actual_row = row - gutter_top.value;
      const row_hints = puzzle_state.definition.meta!.row_hints[actual_row];
      const hint_index = col - (gutter_left.value - row_hints.length);

      if (hint_index >= 0 && hint_index < row_hints.length) {
        const hint = row_hints[hint_index];

        // Check if this gutter cell is marked
        const gutter_index = get_left_gutter_index(actual_row, col);
        const marked = is_marked('left', gutter_index);

        ctx.fillStyle = marked ? "#d1d5db" : "#9ca3af"; // gray-300 if marked, gray-400 if not
        ctx.font = `${size * 0.6}px sans-serif`;
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(hint.toString(), x + size / 2, y + size / 2);
      }
      return;
    }

    // Main grid: render game cells
    // Adjust indices to access board array (which doesn't include gutters)
    const board_row = row - gutter_top.value;
    const board_col = col - gutter_left.value;
    const value = puzzle_state.board[board_row][board_col];

    // Draw cell background (white by default)
    ctx.fillStyle = current_theme.background;
    ctx.fillRect(x, y, size + 1, size + 1);

    // Render cell content
    if (value === KakurasuCell.BLACK) {
      // Black filled cell
      ctx.fillStyle = "#000000";
      ctx.fillRect(x + 3, y + 3, size - 5.2, size - 5.2);
    } else if (value === KakurasuCell.CROSS) {
      // Cross mark
      if (current_cross) {
        const img_size = size * 0.67;
        const offset = (size - img_size) / 2;
        ctx.drawImage(current_cross, x + offset, y + offset, img_size, img_size);
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
    :gutter-top="gutter_top"
    :gutter-left="gutter_left"
    :gutter-top-inside-borders="'vertical'"
    :gutter-left-inside-borders="'horizontal'"
    :outside-border-thickness="5"
  />
</template>
