<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from "vue";
import CanvasBoard from "@/features/gameboard/canvas-board.vue";
import type { CellRenderer } from "@/features/gameboard/canvas-types";
import { MinesweeperCell } from "./useMinesweeperGame";
import type { RuleViolation } from "@/core/games/types/puzzle-types.ts";

const props = defineProps<{
  state: {
    definition: { rows: number; cols: number; initial_state?: number[][] };
    board: number[][];
    violations?: RuleViolation[];
  };
}>();

const emit = defineEmits<{
  (e: "cell-click", row: number, col: number, button: number): void;
  (e: "cell-drag", row: number, col: number): void;
  (e: "cell-enter", row: number, col: number, zone: string): void;
  (e: "cell-leave", row: number, col: number, zone: string): void;
}>();

const hovered_cell = ref<{ row: number; col: number; zone: string } | null>(null);
const canvas_board_ref = ref<InstanceType<typeof CanvasBoard> | null>(null);
const is_dragging = ref(false);
const drag_button = ref<number>(0);
const dragged_cells = ref<Set<string>>(new Set());

const images = ref<Record<string, HTMLImageElement | null>>({
  unopened: null, unopened_highlighted: null, cell_empty: null, cell_violation: null,
  number_0: null, number_1: null, number_2: null, number_3: null,
  number_4: null, number_5: null, number_6: null, number_7: null, number_8: null,
  flag: null, safe: null, question_mark: null,
});
const images_loaded = ref(0);

onMounted(() => {
  const assets: Record<string, string> = {
    unopened: "/assets/minesweeper/unopened-square.svg",
    unopened_highlighted: "/assets/minesweeper/unopened-square-highlighted.svg",
    cell_empty: "/assets/minesweeper/cell-empty.svg",
    cell_violation: "/assets/minesweeper/cell-violation.svg",
    number_0: "/assets/minesweeper/number-0.svg",
    number_1: "/assets/minesweeper/number-1.svg",
    number_2: "/assets/minesweeper/number-2.svg",
    number_3: "/assets/minesweeper/number-3.svg",
    number_4: "/assets/minesweeper/number-4.svg",
    number_5: "/assets/minesweeper/number-5.svg",
    number_6: "/assets/minesweeper/number-6.svg",
    number_7: "/assets/minesweeper/number-7.svg",
    number_8: "/assets/minesweeper/number-8.svg",
    flag: "/assets/minesweeper/flag.svg",
    safe: "/assets/minesweeper/cell-safe.svg",
    question_mark: "/assets/minesweeper/question-mark.svg",
  };
  for (const [key, path] of Object.entries(assets)) {
    const img = new Image();
    img.src = path;
    img.onload = () => { images.value[key] = img; images_loaded.value++; };
  }
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
  const _ = images_loaded.value;
  const current_images = images.value;
  const initial = props.state.definition.initial_state;
  const numRows = props.state.definition.rows;
  const numCols = props.state.definition.cols;

  return (r, cell, row, col, _state) => {
    const value = props.state.board[row][col];

    const has_violation = props.state.violations?.some(
      (v) => v.rule_name === "minesweeper_surrounding_flag_violation" && v.locations?.some((loc) => loc.row === row && loc.col === col),
    );

    // Background based on cell type
    const needs_unopened_bg = value === MinesweeperCell.SAFE || value === MinesweeperCell.FLAG;

    if (needs_unopened_bg) {
      if (current_images.unopened) r.imageCell(cell, current_images.unopened);
    } else if (value !== MinesweeperCell.UNMARKED) {
      const bg_img = has_violation ? current_images.cell_violation : current_images.cell_empty;
      if (bg_img) r.imageCell(cell, bg_img);
    }

    // Foreground content
    if (value === MinesweeperCell.UNMARKED) {
      if (current_images.unopened) r.imageCell(cell, current_images.unopened);
    } else if (value >= MinesweeperCell.EMPTY && value <= MinesweeperCell.EIGHT) {
      let should_draw = value !== MinesweeperCell.EMPTY;
      if (!should_draw && initial) {
        for (let dr = -1; dr <= 1 && !should_draw; dr++) {
          for (let dc = -1; dc <= 1 && !should_draw; dc++) {
            if (dr === 0 && dc === 0) continue;
            const nr = row + dr, nc = col + dc;
            if (nr >= 0 && nr < numRows && nc >= 0 && nc < numCols) {
              if (initial[nr][nc] === -1) should_draw = true;
            }
          }
        }
      }

      if (should_draw) {
        const number_images = [
          current_images.number_0, current_images.number_1, current_images.number_2,
          current_images.number_3, current_images.number_4, current_images.number_5,
          current_images.number_6, current_images.number_7, current_images.number_8,
        ];
        const img = number_images[value];
        if (img) r.imageCentered(cell, img, 1 / 1.3);
      }
    } else if (value === MinesweeperCell.FLAG) {
      if (current_images.flag) r.imageCell(cell, current_images.flag);
    } else if (value === MinesweeperCell.SAFE) {
      if (current_images.safe) r.imageCentered(cell, current_images.safe, 1 / 1.5);
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
    :outside-border-thickness="0"
    outside-border-color="#757575"
    :inside-border-thickness="0"
    grid-color="#757575"
    :gap="0"
    @cell-mousedown="on_cell_mousedown"
    @cell-enter="on_cell_enter"
    @cell-leave="on_cell_leave"
    @board-leave="on_board_leave"
  />
</template>
