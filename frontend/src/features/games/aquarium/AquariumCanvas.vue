<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from "vue";
import CanvasBoard from "@/features/gameboard/canvas-board.vue";
import { useCanvasTheme } from "@/features/gameboard/canvas-theme";
import type { CellRenderer } from "@/features/gameboard/canvas-types";
import { AquariumCell } from "./useAquariumGame";
import type { AquariumMeta } from "./useAquariumGame";
import type { PuzzleState, RuleViolation } from "@/core/games/types/puzzle-types.ts";

const props = defineProps<{
  state: PuzzleState<AquariumMeta>;
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
  if (coord.zone === "leftGutter") { emit("gutter-click", true, coord.row, event.button); return; }
  if (coord.zone === "topGutter") { emit("gutter-click", false, coord.col, event.button); return; }
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

const REGION_BORDER_WIDTH = 3;

const cell_renderer = computed((): CellRenderer => {
  const _ = image_loaded.value;
  const current_theme = theme.value;
  const current_cross = cross_image.value;
  const rows = props.state.definition.rows;
  const cols = props.state.definition.cols;
  const meta = props.state.definition.meta;

  return (r, cell, row, col, _state) => {
    const puzzle_state = props.state;

    // Top gutter: column hints
    if (row === 0 && col >= 1) {
      const board_col = col - 1;
      const col_hint = meta?.col_hints?.[board_col] ?? 0;
      const has_violation = puzzle_state.violations?.some(
        (v) => v.rule_name === "aquarium_col_exceeded" && v.locations?.some((loc) => loc.col === board_col && loc.row === -1)
      );
      r.textCentered(cell, col_hint.toString(), { color: has_violation ? current_theme.error : "#000000", sizeFactor: 0.6, weight: 'bold', font: 'Roboto, sans-serif', offsetY: 2 });
      return;
    }

    // Left gutter: row hints
    if (col === 0 && row >= 1) {
      const board_row = row - 1;
      const row_hint = meta?.row_hints?.[board_row] ?? 0;
      const has_violation = puzzle_state.violations?.some(
        (v) => v.rule_name === "aquarium_row_exceeded" && v.locations?.some((loc) => loc.row === board_row && loc.col === -1)
      );
      r.textCentered(cell, row_hint.toString(), { color: has_violation ? current_theme.error : "#000000", sizeFactor: 0.6, weight: 'bold', font: 'Roboto, sans-serif', offsetY: 2 });
      return;
    }

    // Corner cell
    if (row === 0 && col === 0) return;

    // Main grid
    const board_row = row - 1;
    const board_col = col - 1;
    if (board_row < 0 || board_row >= rows || board_col < 0 || board_col >= cols) return;

    const value = puzzle_state.board[board_row]?.[board_col] ?? AquariumCell.EMPTY;
    const region_map = props.state.definition.meta.regions;

    if (!region_map) {
      r.fillCell(cell, "#ffffff");
      r.strokeCell(cell, "#000000");
      return;
    }

    const has_violation = puzzle_state.violations?.some(
      (v) => v.rule_name === "aquarium_gravity_violation" && v.locations?.some((loc) => loc.row === board_row && loc.col === board_col)
    );

    let bg_color: string;
    if (has_violation) bg_color = "#fca5a5";
    else if (value === AquariumCell.WATER) bg_color = "#60a5fa";
    else bg_color = "#ffffff";

    r.fillCell(cell, bg_color);
    r.strokeCell(cell, "#cfcfcf");

    if (value === AquariumCell.CROSS) {
      r.crossMark(cell, current_cross, { lineColor: current_theme.text });
    }

    r.regionBorders(cell, board_row, board_col, rows, cols, region_map, { border_width: REGION_BORDER_WIDTH });
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
    grid-color="#cfcfcf"
    :inside-border-thickness="0"
    :outside-border-thickness="0"
    :draw-grid-lines="false"
    @cell-mousedown="on_cell_mousedown"
    @cell-enter="on_cell_enter"
    @cell-leave="on_cell_leave"
    @board-leave="on_board_leave"
  />
</template>
