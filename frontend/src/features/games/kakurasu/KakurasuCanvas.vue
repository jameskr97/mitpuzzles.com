<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from "vue";
import CanvasBoard from "@/features/gameboard/canvas-board.vue";
import { useCanvasTheme } from "@/features/gameboard/canvas-theme";
import type { CellRenderer } from "@/features/gameboard/canvas-types";
import { KakurasuCell } from "./useKakurasuGame";
import type { KakurasuMeta, RuleViolation } from "@/core/games/types/puzzle-types.ts";

const props = defineProps<{
  state: {
    definition: { rows: number; cols: number; meta: KakurasuMeta };
    board: number[][];
    violations?: RuleViolation[];
  };
}>();

const emit = defineEmits<{
  (e: "cell-click", row: number, col: number, button: number): void;
  (e: "cell-drag", row: number, col: number): void;
  (e: "cell-enter", row: number, col: number, zone: string): void;
  (e: "cell-leave", row: number, col: number, zone: string): void;
  (e: "gutter-click", is_row: boolean, index: number, button: number): void;
}>();

const hovered_cell = ref<{ row: number; col: number; zone: string } | null>(null);
const { theme } = useCanvasTheme();
const canvas_board_ref = ref<InstanceType<typeof CanvasBoard> | null>(null);
const is_dragging = ref(false);
const drag_button = ref<number>(0);
const dragged_cells = ref<Set<string>>(new Set());

const cross_image = ref<HTMLImageElement | null>(null);
const image_loaded = ref(false);

onMounted(() => {
  const img = new Image();
  img.src = "/assets/kakurasu/cross.svg";
  img.onload = () => { cross_image.value = img; image_loaded.value = true; };
  document.addEventListener("mouseup", stop_drag);
});
onUnmounted(() => { document.removeEventListener("mouseup", stop_drag); });

function on_cell_mousedown(coord: { row: number; col: number; zone: string }, event: MouseEvent) {
  if (coord.zone === "leftGutter") {
    if (coord.row >= 0 && coord.row < props.state.definition.rows) emit("gutter-click", true, coord.row, event.button);
    return;
  }
  if (coord.zone === "topGutter") {
    if (coord.col >= 0 && coord.col < props.state.definition.cols) emit("gutter-click", false, coord.col, event.button);
    return;
  }
  if (coord.zone !== "game") return;
  is_dragging.value = true;
  drag_button.value = event.button;
  dragged_cells.value = new Set([`${coord.row},${coord.col}`]);
  emit("cell-click", coord.row, coord.col, event.button);
}

function on_cell_enter(coord: { row: number; col: number; zone: string }, _event: MouseEvent) {
  hovered_cell.value = { row: coord.row, col: coord.col, zone: coord.zone };
  emit("cell-enter", coord.row, coord.col, coord.zone);
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
  if (hovered_cell.value) emit("cell-leave", hovered_cell.value.row, hovered_cell.value.col, hovered_cell.value.zone);
  hovered_cell.value = null;
}

function stop_drag() { is_dragging.value = false; dragged_cells.value.clear(); }

const cell_renderer = computed((): CellRenderer => {
  // @ts-expect-error reactive dependency trigger
  const _ = image_loaded.value;
  const current_theme = theme.value;
  const current_cross = cross_image.value;

  return (r, cell, row, col, _state) => {
    const puzzle_state = props.state;

    // Top gutter: column numbers
    if (row === 0) {
      r.textCentered(cell, col.toString(), { color: current_theme.hint, sizeFactor: 0.7, font: 'Roboto, sans-serif', offsetY: 3 });
      return;
    }

    // Left gutter: row numbers
    if (col === 0) {
      r.textCentered(cell, row.toString(), { color: current_theme.hint, sizeFactor: 0.7, font: 'Roboto, sans-serif', offsetY: 3 });
      return;
    }

    // Right gutter: row sums
    if (col === 1 + puzzle_state.definition.cols) {
      const board_row = row - 1;
      const row_sum = puzzle_state.definition.meta.row_sums[board_row];
      const has_violation = puzzle_state.violations?.some(
        (v) => v.rule_name === "line_sum_row_exceeded" && v.locations?.some((loc) => loc.row === board_row && loc.col === -1)
      );
      r.textCentered(cell, row_sum.toString(), { color: has_violation ? current_theme.error : current_theme.blue, sizeFactor: 0.7, font: 'Roboto, sans-serif', offsetY: 3 });
      return;
    }

    // Bottom gutter: column sums
    if (row === 1 + puzzle_state.definition.rows) {
      const board_col = col - 1;
      const col_sum = puzzle_state.definition.meta.col_sums[board_col];
      const has_violation = puzzle_state.violations?.some(
        (v) => v.rule_name === "line_sum_col_exceeded" && v.locations?.some((loc) => loc.col === board_col && loc.row === -1)
      );
      r.textCentered(cell, col_sum.toString(), { color: has_violation ? current_theme.error : current_theme.blue, sizeFactor: 0.7, font: 'Roboto, sans-serif', offsetY: 3 });
      return;
    }

    // Main grid
    const board_row = row - 1;
    const board_col = col - 1;
    const value = puzzle_state.board[board_row][board_col];

    r.fillCell(cell, current_theme.background);

    if (value === KakurasuCell.BLACK) {
      r.filledSquare(cell, current_theme.wall);
    } else if (value === KakurasuCell.CROSS) {
      r.crossMark(cell, current_cross, { lineColor: current_theme.text });
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
