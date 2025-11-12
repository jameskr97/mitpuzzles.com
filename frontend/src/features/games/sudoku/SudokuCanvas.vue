<script setup lang="ts">
/**
 * SudokuCanvas - Canvas-based renderer for Sudoku
 */
import { ref, computed, onMounted, onUnmounted } from "vue";
import CanvasBoard from "@/features/gameboard/canvas-board.vue";
import { useCanvasTheme } from "@/features/gameboard/canvas-theme";
import type { CellRenderer } from "@/features/gameboard/canvas-types";
import { SudokuCell } from "./useSudokuGame";
import type { RuleViolation } from "@/types/game-types";

const props = defineProps<{
  state: {
    definition: { rows: number; cols: number; initial_state?: number[][] };
    board: number[][];
    violations?: RuleViolation[];
  };
  is_prefilled?: (row: number, col: number) => boolean;
  box_size?: number;
}>();

// Default is_prefilled: check initial_state if available, otherwise return false
function default_is_prefilled(row: number, col: number): boolean {
  const initial = (props.state.definition as any).initial_state;
  if (!initial || !initial[row]) return false;
  return initial[row][col] !== 0 && initial[row][col] !== SudokuCell.EMPTY;
}

const is_prefilled = computed(() => props.is_prefilled ?? default_is_prefilled);

// Default box_size: 3 for 9x9, calculated for other sizes
const box_size = computed(() => (props.box_size ?? Math.sqrt(props.state.definition.rows)) || 3);

const emit = defineEmits<{
  (e: "cell-click", row: number, col: number): void;
  (e: "cell-key", row: number, col: number, key: string): void;
}>();

const { theme } = useCanvasTheme();
const canvas_board_ref = ref<InstanceType<typeof CanvasBoard> | null>(null);

// Track active cell for highlighting
const active_cell = ref<{ row: number; col: number } | null>(null);

onMounted(() => { document.addEventListener("keydown", on_keydown); });
onUnmounted(() => { document.removeEventListener("keydown", on_keydown); });

function on_cell_mousedown(coord: { row: number; col: number; zone: string }, _event: MouseEvent) {
  if (coord.zone !== "game") return;
  active_cell.value = { row: coord.row, col: coord.col };
  emit("cell-click", coord.row, coord.col);
}

function on_keydown(event: KeyboardEvent) {
  if (!active_cell.value) return;
  const key = event.key;
  if (/^[0-9]$/.test(key) || key === "Backspace" || key === "Delete") {
    emit("cell-key", active_cell.value.row, active_cell.value.col, key);
  }
}

function should_highlight(row: number, col: number): boolean {
  if (!active_cell.value) return false;
  const { row: ar, col: ac } = active_cell.value;
  const bs = box_size.value;
  return (
    row === ar ||
    col === ac ||
    (Math.floor(row / bs) === Math.floor(ar / bs) && Math.floor(col / bs) === Math.floor(ac / bs))
  );
}

function is_active(row: number, col: number): boolean {
  return active_cell.value?.row === row && active_cell.value?.col === col;
}

function has_violation(row: number, col: number): boolean {
  const RULES = ["row_duplicate_violation", "col_duplicate_violation", "box_duplicate_violation"];
  return props.state.violations?.some(
    (v) => RULES.includes(v.rule_name) && v.locations?.some((loc) => loc.row === row && loc.col === col)
  ) ?? false;
}

const cell_renderer = computed((): CellRenderer => {
  const current_theme = theme.value;
  const _ = active_cell.value; // Reactive dependency

  return (ctx, row, col, x, y, size, _state) => {
    const puzzle_state = props.state;
    const value = puzzle_state.board[row][col];

    const highlight = should_highlight(row, col);
    const active = is_active(row, col);
    const prefilled = is_prefilled.value(row, col);
    const is_violation = has_violation(row, col);

    // Background
    if (active) {
      ctx.fillStyle = "#cbd5e1";
    } else if (highlight) {
      ctx.fillStyle = "#e2e8f0";
    } else {
      ctx.fillStyle = current_theme.background;
    }
    ctx.fillRect(x, y, size, size);

    // Number
    if (value !== SudokuCell.EMPTY) {
      if (is_violation) {
        ctx.fillStyle = "#ef4444";
      } else if (prefilled) {
        ctx.fillStyle = "#404040";
      } else {
        ctx.fillStyle = "#0084d1";
      }
      ctx.font = `bold ${size * 0.6}px sans-serif`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(value.toString(), x + size / 2, y + size / 2 + 2);
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
    :outside-border-thickness="4"
    outside-border-color="#6b7280"
    grid-color="#9ca3af"
    :major-grid-every="box_size"
    :major-grid-thickness="3"
    major-grid-color="#6b7280"
    @cell-mousedown="on_cell_mousedown"
  />
</template>
