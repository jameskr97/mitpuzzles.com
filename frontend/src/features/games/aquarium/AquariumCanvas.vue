<script setup lang="ts">
/**
 * AquariumCanvas - Canvas-based renderer for Aquarium
 *
 * Renders a grid with region borders, row/column hints, and water cells.
 */
import { ref, computed, onMounted, onUnmounted } from "vue";
import CanvasBoard from "@/features/gameboard/canvas-board.vue";
import { useCanvasTheme } from "@/features/gameboard/canvas-theme";
import type { CellRenderer } from "@/features/gameboard/canvas-types";
import { draw_region_borders } from "@/features/gameboard/canvas-utils";
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
}>();

// Track hovered cell for hover event recording
const hovered_cell = ref<{ row: number; col: number; zone: string } | null>(null);

const { theme } = useCanvasTheme();

const is_dragging = ref(false);
const drag_button = ref<number>(0);
const dragged_cells = ref<Set<string>>(new Set());

// Preload cross image (same as Kakurasu)
const cross_image = ref<HTMLImageElement | null>(null);
const image_loaded = ref(false);

onMounted(() => {
  const img = new Image();
  img.src = "/assets/kakurasu/cross.svg";
  img.onload = () => {
    cross_image.value = img;
    image_loaded.value = true;
  };
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
  // Emit hover enter for tracking (all zones)
  hovered_cell.value = { row: coord.row, col: coord.col, zone: coord.zone };
  emit("cell-enter", coord.row, coord.col, coord.zone);

  // Handle drag (game zone only)
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
  if (hovered_cell.value) {
    emit("cell-leave", hovered_cell.value.row, hovered_cell.value.col, hovered_cell.value.zone);
  }
  hovered_cell.value = null;
}

function stop_drag() { is_dragging.value = false; dragged_cells.value.clear(); }

// Constants for rendering
const REGION_BORDER_WIDTH = 3;
const CELL_BORDER_WIDTH = 1;

const cell_renderer = computed((): CellRenderer => {
  const _ = image_loaded.value; // Access for reactivity
  const current_theme = theme.value;
  const current_cross = cross_image.value;
  const rows = props.state.definition.rows;
  const cols = props.state.definition.cols;
  const meta = props.state.definition.meta;

  return (ctx, row, col, x, y, size, _state) => {
    const puzzle_state = props.state;

    // Helper function to set up text rendering
    const setup_gutter_text = (color: string) => {
      ctx.fillStyle = color;
      ctx.font = `bold ${size * 0.6}px Roboto, sans-serif`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
    };

    // Top gutter: column hints
    if (row === 0 && col >= 1) {
      const board_col = col - 1;
      const col_hint = meta?.col_hints?.[board_col] ?? 0;
      const has_violation = puzzle_state.violations?.some(
        (v) => v.rule_name === "aquarium_col_exceeded" &&
          v.locations?.some((loc) => loc.col === board_col && loc.row === -1)
      );
      setup_gutter_text(has_violation ? current_theme.error : "#000000");
      ctx.fillText(col_hint.toString(), x + size / 2, y + size / 2 + 2);
      return;
    }

    // Left gutter: row hints
    if (col === 0 && row >= 1) {
      const board_row = row - 1;
      const row_hint = meta?.row_hints?.[board_row] ?? 0;
      const has_violation = puzzle_state.violations?.some(
        (v) => v.rule_name === "aquarium_row_exceeded" &&
          v.locations?.some((loc) => loc.row === board_row && loc.col === -1)
      );
      setup_gutter_text(has_violation ? current_theme.error : "#000000");
      ctx.fillText(row_hint.toString(), x + size / 2, y + size / 2 + 2);
      return;
    }

    // Corner cell (top-left)
    if (row === 0 && col === 0) {
      return;
    }

    // Main grid: adjust indices for board access (subtract gutters)
    const board_row = row - 1;
    const board_col = col - 1;

    // Bounds check
    if (board_row < 0 || board_row >= rows || board_col < 0 || board_col >= cols) {
      return;
    }

    const value = puzzle_state.board[board_row]?.[board_col] ?? AquariumCell.EMPTY;
    const region_map = props.state.definition.meta.regions;

    // Early return if no region data
    if (!region_map) {
      ctx.fillStyle = "#ffffff";
      ctx.fillRect(x, y, size, size);
      ctx.strokeStyle = "#000000";
      ctx.lineWidth = 1;
      ctx.strokeRect(x, y, size, size);
      return;
    }

    // Check for violations
    const has_gravity_violation = puzzle_state.violations?.some(
      (v) => v.rule_name === "aquarium_gravity_violation" &&
        v.locations?.some((loc) => loc.row === board_row && loc.col === board_col)
    );
    const has_violation = has_gravity_violation;

    // Determine cell background color
    let bg_color: string;
    if (has_violation) {
      bg_color = "#fca5a5"; // Red for violations
    } else if (value === AquariumCell.WATER) {
      bg_color = "#60a5fa"; // Blue for water
    } else {
      bg_color = "#ffffff"; // White for empty/cross
    }

    // Draw cell background
    ctx.fillStyle = bg_color;
    ctx.fillRect(x, y, size, size);

    // Draw thin grey cell border (under content, but over background)
    ctx.strokeStyle = "#cfcfcf";
    ctx.lineWidth = 1;
    ctx.strokeRect(x, y, size, size);

    // Draw X mark for CROSS cells (using Kakurasu cross image)
    if (value === AquariumCell.CROSS) {
      if (current_cross) {
        const img_size = size * 0.67;
        const offset = (size - img_size) / 2;
        ctx.drawImage(current_cross, x + offset, y + offset, img_size, img_size);
      } else {
        // Fallback: draw X with lines
        ctx.strokeStyle = current_theme.text;
        ctx.lineWidth = 2;
        const padding = size * 0.17;
        ctx.beginPath();
        ctx.moveTo(x + padding, y + padding);
        ctx.lineTo(x + size - padding, y + size - padding);
        ctx.moveTo(x + size - padding, y + padding);
        ctx.lineTo(x + padding, y + size - padding);
        ctx.stroke();
      }
    }

    // Draw thick region borders on top
    draw_region_borders(ctx, board_row, board_col, x, y, size, rows, cols, region_map, {
      border_width: REGION_BORDER_WIDTH,
    });
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
