<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from "vue";
import CanvasBoard from "@/features/gameboard/canvas-board.vue";
import { useCanvasTheme } from "@/features/gameboard/canvas-theme";
import type { CellRenderer } from "@/features/gameboard/canvas-types";
import { NorinoriCell } from "./useNorinoriGame";
import type { RuleViolation } from "@/core/games/types/puzzle-types";

const props = defineProps<{
  state: {
    definition: { rows: number; cols: number; meta?: { regions: number[][] } };
    board: number[][];
    violations?: RuleViolation[];
  };
  get_region: (row: number, col: number) => number;
  same_region: (r1: number, c1: number, r2: number, c2: number) => boolean;
}>();

const emit = defineEmits<{
  (e: "cell-click", row: number, col: number, button: number): void;
  (e: "cell-drag", row: number, col: number): void;
  (e: "cell-enter", row: number, col: number): void;
  (e: "cell-leave", row: number, col: number): void;
}>();

const hovered_cell = ref<{ row: number; col: number } | null>(null);
const { theme } = useCanvasTheme();
const is_dragging = ref(false);
const drag_button = ref<number>(0);
const dragged_cells = ref<Set<string>>(new Set());

onMounted(() => { document.addEventListener("mouseup", stop_drag); });
onUnmounted(() => { document.removeEventListener("mouseup", stop_drag); });

function on_cell_mousedown(coord: { row: number; col: number; zone: string }, event: MouseEvent) {
  if (coord.zone !== "game") return;
  is_dragging.value = true;
  drag_button.value = event.button;
  dragged_cells.value = new Set([`${coord.row},${coord.col}`]);
  emit("cell-click", coord.row, coord.col, event.button);
}

function on_cell_enter(coord: { row: number; col: number; zone: string }, _event: MouseEvent) {
  hovered_cell.value = { row: coord.row, col: coord.col };
  emit("cell-enter", coord.row, coord.col);
  if (coord.zone !== "game" || !is_dragging.value) return;
  const cell_key = `${coord.row},${coord.col}`;
  if (dragged_cells.value.has(cell_key)) return;
  dragged_cells.value.add(cell_key);
  emit("cell-drag", coord.row, coord.col);
}

function on_cell_leave(coord: { row: number; col: number; zone: string }, _event: MouseEvent) {
  emit("cell-leave", coord.row, coord.col);
}

function on_board_leave(_event: MouseEvent) {
  if (hovered_cell.value) emit("cell-leave", hovered_cell.value.row, hovered_cell.value.col);
  hovered_cell.value = null;
}

function stop_drag() { is_dragging.value = false; dragged_cells.value.clear(); }

const REGION_BORDER_WIDTH = 3;

const cell_renderer = computed((): CellRenderer => {
  const _current_theme = theme.value;
  const rows = props.state.definition.rows;
  const cols = props.state.definition.cols;

  return (r, cell, row, col, _state) => {
    const puzzle_state = props.state;
    const value = puzzle_state.board[row][col];
    const region_map = puzzle_state.definition.meta?.regions;

    if (!region_map) {
      r.fillCell(cell, "#ffffff");
      r.strokeCell(cell, "#000000");
      return;
    }

    const has_domino_violation = puzzle_state.violations?.some(
      (v) => v.rule_name === "norinori_domino_violation" && v.locations?.some((loc) => loc.row === row && loc.col === col)
    );
    const has_region_violation = puzzle_state.violations?.some(
      (v) => v.rule_name === "norinori_region_count_violation" && v.locations?.some((loc) => loc.row === row && loc.col === col)
    );
    const has_violation = has_domino_violation || has_region_violation;

    let bg_color: string;
    if (has_violation) bg_color = "#fca5a5";
    else if (value === NorinoriCell.SHADED) bg_color = "#999";
    else bg_color = "#ffffff";

    r.fillCell(cell, bg_color);

    if (value === NorinoriCell.CROSS) {
      r.crossMark(cell, null, { linePadding: 0.25, lineColor: "#9ca3af", lineWidth: 2 });
    }

    r.strokeCell(cell, "#797979");
    r.regionBorders(cell, row, col, rows, cols, region_map, { border_width: REGION_BORDER_WIDTH });
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
    grid-color="#000"
    outside-border-color="#000"
    :inside-border-thickness="2"
    :outside-border-thickness="3"
    @cell-mousedown="on_cell_mousedown"
    @cell-enter="on_cell_enter"
    @cell-leave="on_cell_leave"
    @board-leave="on_board_leave"
  />
</template>
