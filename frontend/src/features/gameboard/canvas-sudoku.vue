<script setup lang="ts">
import { computed, ref, onMounted } from "vue";
import CanvasBoard from "./canvas-board.vue";
import { useCanvasTheme } from "./canvas-theme";
import type { PuzzleState, SudokuMeta } from "@/services/game/engines/types";
import type { createPuzzleInteractionBridge } from "@/features/games.composables/setupPuzzleInteractionBridge";
import type { CellRenderer } from "./canvas-types";
import type { Cell } from "@/features/games.components/board.interaction.ts";

// Props
const props = defineProps<{
  state: PuzzleState<SudokuMeta>;
  interact?: ReturnType<typeof createPuzzleInteractionBridge>;
}>();

const { theme } = useCanvasTheme();

// Local state for cell highlighting
const active_cell = ref<Cell | null>(null);
const subgrid_size = computed(() => Math.sqrt(props.state.definition.rows));

// Helper to check if a cell matches the active cell (same row/col/box)
function is_cell_match(cell: Cell | null, row: number, col: number) {
  if (!cell) return { row: false, col: false, box: false };
  const size = subgrid_size.value;
  return {
    row: cell.row === row,
    col: cell.col === col,
    box:
      Math.floor(cell.row / size) === Math.floor(row / size) &&
      Math.floor(cell.col / size) === Math.floor(col / size),
  };
}

// Helper to check if a cell should be highlighted
function should_highlight_cell(row: number, col: number): boolean {
  const match = is_cell_match(active_cell.value, row, col);
  return match.row || match.col || match.box;
}

// Helper to check if a cell is active
function is_cell_active(row: number, col: number): boolean {
  return active_cell.value?.row === row && active_cell.value?.col === col;
}

// Helper to check if a cell is prefilled
function is_prefilled(row: number, col: number): boolean {
  return props.state.definition.initial_state[row][col] !== -1;
}

// Helper to check for violations on a cell
function has_violation(row: number, col: number): boolean {
  const RULES = ["row_duplicate_violation", "col_duplicate_violation", "box_duplicate_violation"];
  return props.state.violations?.some(
    (v) => RULES.includes(v.rule_name) &&
           v.locations?.some((loc) => loc.row === row && loc.col === col)
  ) ?? false;
}

// Register inline behavior to track cell clicks
onMounted(() => {
  if (props.interact) {
    props.interact.addInputBehaviour(() => ({
      onCellMouseDown(cell: Cell, _event: MouseEvent): boolean {
        active_cell.value = cell;
        return false; // Allow other behaviors to handle the event
      },
    }));
  }
});

// Sudoku cell renderer
const cell_renderer = computed((): CellRenderer => {
  const current_theme = theme.value;
  // Access active_cell.value to create reactive dependency
  const _ = active_cell.value;

  return (ctx, row, col, x, y, size, state) => {
    const puzzle_state = state as PuzzleState<SudokuMeta>;
    const value = puzzle_state.board[row][col];

    // Check highlighting state using local functions
    const should_highlight = should_highlight_cell(row, col);
    const is_active = is_cell_active(row, col);
    const prefilled = is_prefilled(row, col);
    const is_violation = has_violation(row, col);

    // Draw cell background
    if (is_active) {
      // Active cell gets darker gray background (slate-300)
      ctx.fillStyle = "#cbd5e1";
      ctx.fillRect(x, y, size, size);
    } else if (should_highlight) {
      // Highlighted cells (same row/col/box) get lighter gray (slate-200)
      ctx.fillStyle = "#e2e8f0";
      ctx.fillRect(x, y, size, size);
    } else {
      // Default white background
      ctx.fillStyle = current_theme.background;
      ctx.fillRect(x, y, size, size);
    }

    // Draw number if not empty (0)
    if (value !== 0) {
      // Determine text color
      if (is_violation) {
        // Violations are red
        ctx.fillStyle = "#ef4444"; // red-500
      } else if (prefilled) {
        // Prefilled numbers are black
        ctx.fillStyle = "#404040";
      } else {
        // User-entered numbers are blue (sky-600)
        ctx.fillStyle = "#0084d1";
      }

      ctx.font = `bold ${size * 0.6}px sans-serif`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(value.toString(), x + size / 2, (y + size / 2) + 2);
    }
  };
});

// Calculate box size for major grid lines
const box_size = computed(() => Math.sqrt(props.state.definition.cols));
</script>

<template>
  <CanvasBoard
    :rows="state.definition.rows"
    :cols="state.definition.cols"
    :state="state"
    :interact="interact"
    :cell-renderer="cell_renderer"
    :gap="1"
    :outside-border-thickness="4"
    outside-border-color="#6b7280"
    grid-color="#9ca3af"
    :major-grid-every="box_size"
    :major-grid-thickness="3"
    major-grid-color="#6b7280"
  />
</template>
