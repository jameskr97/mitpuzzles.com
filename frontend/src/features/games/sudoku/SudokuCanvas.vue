<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from "vue";
import CanvasBoard from "@/features/gameboard/canvas-board.vue";
import { useCanvasTheme } from "@/features/gameboard/canvas-theme";
import type { CellRenderer } from "@/features/gameboard/canvas-types";
import { SudokuCell } from "./useSudokuGame";
import type { RuleViolation } from "@/core/games/types/puzzle-types";

const props = withDefaults(defineProps<{
  state: {
    definition: { rows: number; cols: number; initial_state?: number[][] };
    board: number[][];
    violations?: RuleViolation[];
  };
  is_prefilled?: (row: number, col: number) => boolean;
  box_size?: number;
  correct_cells?: Array<{ row: number; col: number }>;
  incorrect_cells?: Array<{ row: number; col: number }>;
  interactive?: boolean;
  blur_mode?: boolean;
  hover_highlight?: boolean;
  highlight_row?: number;
  highlight_col?: number;
  highlight_box?: number;
  highlight_cells?: Array<{ row: number; col: number; color?: string; text_color?: string }>;
}>(), { interactive: true, hover_highlight: false });

function default_is_prefilled(row: number, col: number): boolean {
  const initial = props.state.definition.initial_state;
  if (!initial || !initial[row]) return false;
  return initial[row][col] !== SudokuCell.EMPTY;
}

const is_prefilled = computed(() => props.is_prefilled ?? default_is_prefilled);
const box_size = computed(() => (props.box_size ?? Math.sqrt(props.state.definition.rows)) || 3);

const emit = defineEmits<{
  (e: "cell-click", row: number, col: number): void;
  (e: "cell-key", row: number, col: number, key: string): void;
  (e: "cell-enter", row: number, col: number, zone: string): void;
  (e: "cell-leave", row: number, col: number, zone: string): void;
}>();

const { theme } = useCanvasTheme();
const canvas_board_ref = ref<InstanceType<typeof CanvasBoard> | null>(null);
const active_cell = ref<{ row: number; col: number } | null>(null);
const hovered_cell = ref<{ row: number; col: number; zone: string } | null>(null);
const focused_cell = ref<{ row: number; col: number } | null>(null);

function is_cell_visible_in_blur_mode(row: number, col: number): boolean {
  if (!props.blur_mode) return true;
  if (!focused_cell.value) return false;
  const { row: fr, col: fc } = focused_cell.value;
  const bs = box_size.value;
  return row === fr || col === fc ||
    (Math.floor(row / bs) === Math.floor(fr / bs) && Math.floor(col / bs) === Math.floor(fc / bs));
}

onMounted(() => { document.addEventListener("keydown", on_keydown); });
onUnmounted(() => { document.removeEventListener("keydown", on_keydown); });

watch(focused_cell, () => { if (props.blur_mode && canvas_board_ref.value) canvas_board_ref.value.redraw(); });
watch(hovered_cell, () => { if (canvas_board_ref.value) canvas_board_ref.value.redraw(); });

function on_cell_mousedown(coord: { row: number; col: number; zone: string }, _event: MouseEvent) {
  if (!is_interactive.value) return;
  if (coord.zone !== "game") return;
  active_cell.value = { row: coord.row, col: coord.col };
  if (props.blur_mode) focused_cell.value = { row: coord.row, col: coord.col };
  emit("cell-click", coord.row, coord.col);
}

function on_keydown(event: KeyboardEvent) {
  if (!is_interactive.value || !active_cell.value) return;
  const key = event.key;
  if (/^[0-9]$/.test(key) || key === "Backspace" || key === "Delete") {
    emit("cell-key", active_cell.value.row, active_cell.value.col, key);
  }
}

function on_cell_enter(coord: { row: number; col: number; zone: string }, _event: MouseEvent) {
  emit("cell-enter", coord.row, coord.col, coord.zone);
  if (coord.zone !== "game") { hovered_cell.value = null; return; }
  hovered_cell.value = { row: coord.row, col: coord.col, zone: coord.zone };
}

function on_cell_leave(coord: { row: number; col: number; zone: string }, _event: MouseEvent) {
  emit("cell-leave", coord.row, coord.col, coord.zone);
}

function on_board_leave(_event: MouseEvent) {
  if (hovered_cell.value) emit("cell-leave", hovered_cell.value.row, hovered_cell.value.col, hovered_cell.value.zone);
  hovered_cell.value = null;
}

function should_hover_highlight(row: number, col: number): boolean {
  if (!props.hover_highlight || !hovered_cell.value) return false;
  const { row: hr, col: hc } = hovered_cell.value;
  const bs = box_size.value;
  return row === hr || col === hc ||
    (Math.floor(row / bs) === Math.floor(hr / bs) && Math.floor(col / bs) === Math.floor(hc / bs));
}

function should_highlight(row: number, col: number): boolean {
  if (!active_cell.value) return false;
  const { row: ar, col: ac } = active_cell.value;
  const bs = box_size.value;
  return row === ar || col === ac ||
    (Math.floor(row / bs) === Math.floor(ar / bs) && Math.floor(col / bs) === Math.floor(ac / bs));
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

function is_correct_cell(row: number, col: number): boolean {
  return props.correct_cells?.some((c) => c.row === row && c.col === col) ?? false;
}

function is_incorrect_cell(row: number, col: number): boolean {
  return props.incorrect_cells?.some((c) => c.row === row && c.col === col) ?? false;
}

function is_persistent_highlight(row: number, col: number): boolean {
  const bs = box_size.value;
  if (props.highlight_row !== undefined && row === props.highlight_row) return true;
  if (props.highlight_col !== undefined && col === props.highlight_col) return true;
  if (props.highlight_box !== undefined) {
    const box_index = Math.floor(row / bs) * bs + Math.floor(col / bs);
    if (box_index === props.highlight_box) return true;
  }
  return false;
}

function get_cell_highlight(row: number, col: number): { color?: string; text_color?: string } | null {
  return props.highlight_cells?.find((c) => c.row === row && c.col === col) ?? null;
}

const is_interactive = computed(() => props.interactive !== false);

const cell_renderer = computed((): CellRenderer => {
  const current_theme = theme.value;
  const _ = active_cell.value;
  const __ = props.correct_cells;
  const ___ = props.incorrect_cells;
  const ____ = focused_cell.value;
  const _____ = hovered_cell.value;
  const ______ = props.highlight_row;
  const _______ = props.highlight_col;
  const ________ = props.highlight_box;
  const _________ = props.highlight_cells;
  const blur_enabled = props.blur_mode;

  return (r, cell, row, col, _state) => {
    const puzzle_state = props.state;
    const prefilled = is_prefilled.value(row, col);
    const initial = puzzle_state.definition.initial_state;
    const value = prefilled && initial ? initial[row][col] : puzzle_state.board[row][col];

    const highlight = should_highlight(row, col);
    const hover_highlight = should_hover_highlight(row, col);
    const persistent_highlight = is_persistent_highlight(row, col);
    const cell_highlight = get_cell_highlight(row, col);
    const active = is_active(row, col);
    const is_violation = has_violation(row, col);
    const is_correct = is_correct_cell(row, col);
    const is_incorrect = is_incorrect_cell(row, col);
    const is_visible = is_cell_visible_in_blur_mode(row, col);

    // Background
    let bg_color: string;
    if (is_correct) bg_color = "#bbf7d0";
    else if (is_incorrect) bg_color = "#fecaca";
    else if (active) bg_color = "#cbd5e1";
    else if (highlight) bg_color = "#e2e8f0";
    else if (persistent_highlight) bg_color = "#fff085";
    else if (hover_highlight) bg_color = "#fefce8";
    else bg_color = current_theme.background;

    r.fillCell(cell, bg_color);

    if (cell_highlight?.color) {
      r.strokeRectInset(cell, cell_highlight.color, 1.5);
    }

    // Blur
    const is_blurred = blur_enabled && !is_visible;

    const draw_text = () => {
      if (value === SudokuCell.EMPTY) return;

      let text_color: string;
      if (is_blurred) text_color = "#404040";
      else if (cell_highlight?.text_color) text_color = cell_highlight.text_color;
      else if (is_violation || is_incorrect) text_color = "#ef4444";
      else if (is_correct) text_color = "#16a34a";
      else if (prefilled) text_color = "#404040";
      else text_color = "#0084d1";

      r.textCentered(cell, is_blurred ? "X" : value.toString(), { color: text_color, offsetY: 2 });
    };

    if (is_blurred) {
      r.withFilter("blur(15px)", draw_text);
    } else {
      draw_text();
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
    @cell-enter="on_cell_enter"
    @cell-leave="on_cell_leave"
    @board-leave="on_board_leave"
  />
</template>
