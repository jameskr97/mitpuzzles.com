<script setup lang="ts">
/**
 * SudokuCanvas - Canvas-based renderer for Sudoku
 */
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
  // Persistent highlighting for instructions/demos
  highlight_row?: number;
  highlight_col?: number;
  highlight_box?: number;
  highlight_cells?: Array<{ row: number; col: number; color?: string; text_color?: string }>;
}>(), { interactive: true, hover_highlight: false });

// Default is_prefilled: check initial_state if available, otherwise return false
function default_is_prefilled(row: number, col: number): boolean {
  const initial = props.state.definition.initial_state;
  if (!initial || !initial[row]) return false;
  // In research format, -1 means empty, so anything else is prefilled
  return initial[row][col] !== SudokuCell.EMPTY;
}

const is_prefilled = computed(() => props.is_prefilled ?? default_is_prefilled);

// Default box_size: 3 for 9x9, calculated for other sizes
const box_size = computed(() => (props.box_size ?? Math.sqrt(props.state.definition.rows)) || 3);

const emit = defineEmits<{
  (e: "cell-click", row: number, col: number): void;
  (e: "cell-key", row: number, col: number, key: string): void;
  (e: "cell-enter", row: number, col: number, zone: string): void;
  (e: "cell-leave", row: number, col: number, zone: string): void;
}>();

const { theme } = useCanvasTheme();
const canvas_board_ref = ref<InstanceType<typeof CanvasBoard> | null>(null);

// Track active cell for highlighting (clicked cell)
const active_cell = ref<{ row: number; col: number } | null>(null);

// Track hovered cell for hover highlighting (also stores zone for event emission)
const hovered_cell = ref<{ row: number; col: number; zone: string } | null>(null);

// Track focused cell for blur mode (persists until another cell is focused)
const focused_cell = ref<{ row: number; col: number } | null>(null);

// Check if cell is visible in blur mode (same row/col/box as focused cell)
function is_cell_visible_in_blur_mode(row: number, col: number): boolean {
  if (!props.blur_mode) return true;
  if (!focused_cell.value) return false;

  const { row: fr, col: fc } = focused_cell.value;
  const bs = box_size.value;

  // Same row, column, or box
  return (
    row === fr ||
    col === fc ||
    (Math.floor(row / bs) === Math.floor(fr / bs) && Math.floor(col / bs) === Math.floor(fc / bs))
  );
}

onMounted(() => { document.addEventListener("keydown", on_keydown); });
onUnmounted(() => { document.removeEventListener("keydown", on_keydown); });

// Force redraw when focused_cell changes (for blur mode)
watch(focused_cell, () => {
  if (props.blur_mode && canvas_board_ref.value) {
    canvas_board_ref.value.redraw();
  }
});

// Force redraw when hovered_cell changes (for hover highlighting)
watch(hovered_cell, () => {
  if (canvas_board_ref.value) {
    canvas_board_ref.value.redraw();
  }
});

function on_cell_mousedown(coord: { row: number; col: number; zone: string }, _event: MouseEvent) {
  if (!is_interactive.value) return;
  if (coord.zone !== "game") return;
  active_cell.value = { row: coord.row, col: coord.col };

  // In blur mode, clicking sets the focused cell (reveals that row/col/box)
  if (props.blur_mode) {
    focused_cell.value = { row: coord.row, col: coord.col };
  }

  emit("cell-click", coord.row, coord.col);
}

function on_keydown(event: KeyboardEvent) {
  if (!is_interactive.value) return;
  if (!active_cell.value) return;
  const key = event.key;
  if (/^[0-9]$/.test(key) || key === "Backspace" || key === "Delete") {
    emit("cell-key", active_cell.value.row, active_cell.value.col, key);
  }
}

function on_cell_enter(coord: { row: number; col: number; zone: string }, _event: MouseEvent) {
  // Emit hover enter for tracking (all zones)
  emit("cell-enter", coord.row, coord.col, coord.zone);

  // Visual highlighting only for game zone
  if (coord.zone !== "game") {
    hovered_cell.value = null;
    return;
  }
  hovered_cell.value = { row: coord.row, col: coord.col, zone: coord.zone };
}

function on_cell_leave(coord: { row: number; col: number; zone: string }, _event: MouseEvent) {
  emit("cell-leave", coord.row, coord.col, coord.zone);
}

function on_board_leave(_event: MouseEvent) {
  // Emit leave for current hovered cell before clearing
  if (hovered_cell.value) {
    emit("cell-leave", hovered_cell.value.row, hovered_cell.value.col, hovered_cell.value.zone);
  }
  hovered_cell.value = null;
}

function should_hover_highlight(row: number, col: number): boolean {
  if (!props.hover_highlight) return false;
  if (!hovered_cell.value) return false;
  const { row: hr, col: hc } = hovered_cell.value;
  const bs = box_size.value;
  return (
    row === hr ||
    col === hc ||
    (Math.floor(row / bs) === Math.floor(hr / bs) && Math.floor(col / bs) === Math.floor(hc / bs))
  );
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

function is_correct_cell(row: number, col: number): boolean {
  return props.correct_cells?.some((c) => c.row === row && c.col === col) ?? false;
}

function is_incorrect_cell(row: number, col: number): boolean {
  return props.incorrect_cells?.some((c) => c.row === row && c.col === col) ?? false;
}

function is_persistent_highlight(row: number, col: number): boolean {
  const bs = box_size.value;
  // Check row highlight
  if (props.highlight_row !== undefined && row === props.highlight_row) return true;
  // Check col highlight
  if (props.highlight_col !== undefined && col === props.highlight_col) return true;
  // Check box highlight
  if (props.highlight_box !== undefined) {
    const box_row = Math.floor(row / bs);
    const box_col = Math.floor(col / bs);
    const box_index = box_row * bs + box_col;
    if (box_index === props.highlight_box) return true;
  }
  return false;
}

function get_cell_highlight(row: number, col: number): { color?: string; text_color?: string } | null {
  const cell = props.highlight_cells?.find((c) => c.row === row && c.col === col);
  return cell ?? null;
}

const is_interactive = computed(() => props.interactive !== false);

const cell_renderer = computed((): CellRenderer => {
  const current_theme = theme.value;
  const _ = active_cell.value; // Reactive dependency
  const __ = props.correct_cells; // Reactive dependency
  const ___ = props.incorrect_cells; // Reactive dependency
  const ____ = focused_cell.value; // Reactive dependency for blur mode
  const _____ = hovered_cell.value; // Reactive dependency for hover
  const ______ = props.highlight_row; // Reactive dependency
  const _______ = props.highlight_col; // Reactive dependency
  const ________ = props.highlight_box; // Reactive dependency
  const _________ = props.highlight_cells; // Reactive dependency
  const blur_enabled = props.blur_mode; // Reactive dependency

  return (ctx, row, col, x, y, size, _state) => {
    const puzzle_state = props.state;
    const prefilled = is_prefilled.value(row, col);
    // For prefilled cells, show initial_state value; otherwise show board value
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

    // Background - validation colors take priority
    if (is_correct) {
      ctx.fillStyle = "#bbf7d0"; // green-200
    } else if (is_incorrect) {
      ctx.fillStyle = "#fecaca"; // red-200
    } else if (active) {
      ctx.fillStyle = "#cbd5e1"; // slate-300
    } else if (highlight) {
      ctx.fillStyle = "#e2e8f0"; // slate-200
    } else if (persistent_highlight) {
      ctx.fillStyle = "#fff085";
    } else if (hover_highlight) {
      ctx.fillStyle = "#fefce8"; // yellow-50
    } else {
      ctx.fillStyle = current_theme.background;
    }
    ctx.fillRect(x, y, size, size);

    // Draw cell highlight border if specified
    if (cell_highlight?.color) {
      ctx.strokeStyle = cell_highlight.color;
      ctx.lineWidth = 3;
      ctx.strokeRect(x + 1.5, y + 1.5, size - 3, size - 3);
    }

    // Apply blur filter for non-visible cells in blur mode
    const is_blurred = blur_enabled && !is_visible;
    if (is_blurred) {
      ctx.filter = "blur(15px)";
    }

    // Number (show "X" for blurred cells with values)
    // In research format, -1 means empty
    if (value !== SudokuCell.EMPTY) {
      if (is_blurred) {
        ctx.fillStyle = "#404040";
      } else if (cell_highlight?.text_color) {
        ctx.fillStyle = cell_highlight.text_color;
      } else if (is_violation || is_incorrect) {
        ctx.fillStyle = "#ef4444";
      } else if (is_correct) {
        ctx.fillStyle = "#16a34a"; // green-600
      } else if (prefilled) {
        ctx.fillStyle = "#404040";
      } else {
        ctx.fillStyle = "#0084d1";
      }
      ctx.font = `bold ${size * 0.6}px sans-serif`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(is_blurred ? "X" : value.toString(), x + size / 2, y + size / 2 + 2);
    }

    // Reset filter
    if (is_blurred) {
      ctx.filter = "none";
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
