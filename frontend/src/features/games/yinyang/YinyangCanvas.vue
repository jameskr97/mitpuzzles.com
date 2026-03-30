<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from "vue";
import CanvasBoard from "@/features/gameboard/canvas-board.vue";
import { useCanvasTheme } from "@/features/gameboard/canvas-theme";
import type { CellRenderer } from "@/features/gameboard/canvas-types";
import { YinyangCell } from "./useYinyangGame";
import type { RuleViolation } from "@/core/games/types/puzzle-types";

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

function is_clue_cell(row: number, col: number): boolean {
  const initial = props.state.definition.initial_state;
  if (!initial || !initial[row]) return false;
  const val = initial[row][col];
  return val === YinyangCell.CLUE_BLACK || val === YinyangCell.CLUE_WHITE;
}

const cell_renderer = computed((): CellRenderer => {
  // @ts-expect-error reactive dependency trigger
  const current_theme = theme.value;

  return (r, cell, row, col, _state) => {
    const puzzle_state = props.state;
    const value = puzzle_state.board[row][col];

    const has_violation = puzzle_state.violations?.some(
      (v) => v.rule_name === "yinyang_2x2_violation" && v.locations?.some((loc) => loc.row === row && loc.col === col)
    );

    r.fillCell(cell, "#dcb35c", 0);

    if (value === YinyangCell.EMPTY) return;

    const ctx = r.getContext();
    const radius = cell.size * 0.38;
    const is_clue = is_clue_cell(row, col);

    // go-stone style gradient: highlight from top-left to bottom-right
    const gx0 = cell.cx - radius * 0.3;
    const gy0 = cell.cy - radius * 0.5;
    const gx1 = cell.cx + radius * 0.5;
    const gy1 = cell.cy + radius * 0.5;

    const grad = ctx.createLinearGradient(gx0, gy0, gx1, gy1);
    if (value === YinyangCell.BLACK) {
      grad.addColorStop(0, "hsl(8, 7%, 27%)");
      grad.addColorStop(1, "hsl(8, 7%, 12%)");
    } else {
      grad.addColorStop(0, "hsl(8, 7%, 95%)");
      grad.addColorStop(0.9, "hsl(226, 7%, 75%)");
    }

    // drop shadow
    ctx.save();
    ctx.shadowColor = "rgba(0, 0, 0, 0.7)";
    ctx.shadowBlur = radius * 1.5;
    ctx.shadowOffsetX = radius * 0.5;
    ctx.shadowOffsetY = radius * 0.5;
    ctx.beginPath();
    ctx.arc(cell.cx, cell.cy, radius, 0, Math.PI * 2);
    ctx.fillStyle = grad;
    ctx.fill();
    ctx.restore();

    ctx.beginPath();
    ctx.arc(cell.cx, cell.cy, radius, 0, Math.PI * 2);
    ctx.strokeStyle = has_violation ? "#ef4444" : "hsl(8, 7%, 20%)";
    ctx.lineWidth = has_violation ? 3 : 0.8;
    ctx.stroke();

    if (is_clue) {
      ctx.beginPath();
      ctx.arc(cell.cx, cell.cy, radius * 0.13, 0, Math.PI * 2);
      ctx.fillStyle = value === YinyangCell.BLACK ? "#ffffff" : "#1a1a1a";
      ctx.fill();
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
    :gap="1"
    grid-color="#1a1a1a"
    outside-border-color="#1a1a1a"
    :inside-border-thickness="1"
    :outside-border-thickness="2"
    @cell-mousedown="on_cell_mousedown"
    @cell-enter="on_cell_enter"
    @cell-leave="on_cell_leave"
    @board-leave="on_board_leave"
  />
</template>
