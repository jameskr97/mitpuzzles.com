<script setup lang="ts">
/**
 * NonogramsCanvas - Canvas-based renderer for Nonograms
 */
import { ref, computed, onMounted, onUnmounted } from "vue";
import CanvasBoard from "@/features/gameboard/canvas-board.vue";
import { useCanvasTheme } from "@/features/gameboard/canvas-theme";
import type { CellRenderer } from "@/features/gameboard/canvas-types";
import { NonogramsCell } from "./useNonogramsGame";
import type { NonogramMeta, RuleViolation } from "@/core/games/types/puzzle-types.ts";

const props = defineProps<{
  state: {
    definition: { rows: number; cols: number; meta: NonogramMeta };
    board: number[][];
    violations?: RuleViolation[];
  };
}>();

const emit = defineEmits<{
  (e: "cell-click", row: number, col: number, button: number): void;
  (e: "cell-drag", row: number, col: number): void;
}>();

const { theme } = useCanvasTheme();

const is_dragging = ref(false);
const drag_button = ref<number>(0);
const dragged_cells = ref<Set<string>>(new Set());

const cross_image = ref<HTMLImageElement | null>(null);

// Calculate gutter sizes
const longest_array = (array: number[][]) => array.reduce((a, b) => (b.length > a.length ? b : a), []);
const gutter_left = computed(() => longest_array(props.state.definition.meta.row_hints).length);
const gutter_top = computed(() => longest_array(props.state.definition.meta.col_hints).length);

onMounted(() => {
  const img = new Image();
  img.src = "/assets/kakurasu/cross.svg";
  img.onload = () => { cross_image.value = img; };
  document.addEventListener("mouseup", stop_drag);
});

onUnmounted(() => { document.removeEventListener("mouseup", stop_drag); });

function on_cell_mousedown(coord: { row: number; col: number; zone: string }, event: MouseEvent) {
  if (coord.zone !== "game") return;
  is_dragging.value = true;
  drag_button.value = event.button;
  dragged_cells.value = new Set([`${coord.row},${coord.col}`]);
  emit("cell-click", coord.row, coord.col, event.button);
}

function on_cell_enter(coord: { row: number; col: number; zone: string }, _event: MouseEvent) {
  if (coord.zone !== "game" || !is_dragging.value) return;
  const cell_key = `${coord.row},${coord.col}`;
  if (dragged_cells.value.has(cell_key)) return;
  dragged_cells.value.add(cell_key);
  emit("cell-drag", coord.row, coord.col);
}

function stop_drag() { is_dragging.value = false; dragged_cells.value.clear(); }

const cell_renderer = computed((): CellRenderer => {
  const current_theme = theme.value;
  const current_cross = cross_image.value;
  const gt = gutter_top.value;
  const gl = gutter_left.value;

  return (ctx, row, col, x, y, size, _state) => {
    const puzzle_state = props.state;

    // Top gutter: column hints
    if (row < gt) {
      ctx.fillStyle = current_theme.background;
      ctx.fillRect(x, y, size + 1, size + 1);

      const actual_col = col - gl;
      const col_hints = puzzle_state.definition.meta.col_hints[actual_col];
      const hint_index = row - (gt - col_hints.length);

      if (hint_index >= 0 && hint_index < col_hints.length) {
        ctx.fillStyle = "#9ca3af";
        ctx.font = `${size * 0.6}px sans-serif`;
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(col_hints[hint_index].toString(), x + size / 2, y + size / 2);
      }
      return;
    }

    // Left gutter: row hints
    if (col < gl) {
      ctx.fillStyle = current_theme.background;
      ctx.fillRect(x, y, size + 1, size + 1);

      const actual_row = row - gt;
      const row_hints = puzzle_state.definition.meta.row_hints[actual_row];
      const hint_index = col - (gl - row_hints.length);

      if (hint_index >= 0 && hint_index < row_hints.length) {
        ctx.fillStyle = "#9ca3af";
        ctx.font = `${size * 0.6}px sans-serif`;
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(row_hints[hint_index].toString(), x + size / 2, y + size / 2);
      }
      return;
    }

    // Main grid
    const board_row = row - gt;
    const board_col = col - gl;
    const value = puzzle_state.board[board_row][board_col];

    ctx.fillStyle = current_theme.background;
    ctx.fillRect(x, y, size + 1, size + 1);

    if (value === NonogramsCell.BLACK) {
      ctx.fillStyle = current_theme.wall;
      const outline_width = 2;
      const ow2 = outline_width * 2;
      ctx.fillRect(x + outline_width, y + outline_width, size - ow2, size - ow2);
    } else if (value === NonogramsCell.CROSS && current_cross) {
      const img_size = size * 0.67;
      const offset = (size - img_size) / 2;
      ctx.drawImage(current_cross, x + offset, y + offset, img_size, img_size);
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
    :gutter-top="gutter_top"
    :gutter-left="gutter_left"
    :gutter-top-inside-borders="'vertical'"
    :gutter-left-inside-borders="'horizontal'"
    :outside-border-thickness="5"
    @cell-mousedown="on_cell_mousedown"
    @cell-enter="on_cell_enter"
  />
</template>
