<script setup lang="ts">
/**
 * LightupCanvas - Canvas-based renderer for Lightup (Akari)
 *
 * Clean event-based interface - emits cell-click events.
 * No dependency on old interaction bridge.
 */
import { ref, computed, onMounted, onUnmounted } from "vue";
import CanvasBoard from "@/features/gameboard/canvas-board.vue";
import { useCanvasTheme } from "@/features/gameboard/canvas-theme";
import type { CellRenderer } from "@/features/gameboard/canvas-types";
import { LightupCell, WALL_STATES, NUMBERED_WALLS, compute_lit_cells } from "./useLightupGame";
import type { RuleViolation } from "@/types/game-types";

// Props
const props = defineProps<{
  state: {
    definition: { rows: number; cols: number };
    board: number[][];
    violations?: RuleViolation[];
    lit_cells?: boolean[];
  };
}>();

// Events
const emit = defineEmits<{
  (e: "cell-click", row: number, col: number, button: number): void;
  (e: "cell-drag", row: number, col: number): void;
}>();

// Theme support
const { theme } = useCanvasTheme();

// Canvas board ref
const canvas_board_ref = ref<InstanceType<typeof CanvasBoard> | null>(null);

// Drag state for click-and-drag support
const is_dragging = ref(false);
const drag_button = ref<number>(0);
const dragged_cells = ref<Set<string>>(new Set());

// Preload images
const bulb_image = ref<HTMLImageElement | null>(null);
const bulb_violation_image = ref<HTMLImageElement | null>(null);
const cross_image = ref<HTMLImageElement | null>(null);
const images_loaded = ref(0);

onMounted(() => {
  const bulb_img = new Image();
  bulb_img.src = "/assets/lightup/bulb.svg";
  bulb_img.onload = () => {
    bulb_image.value = bulb_img;
    images_loaded.value++;
  };

  const bulb_violation_img = new Image();
  bulb_violation_img.src = "/assets/lightup/bulb-violation.svg";
  bulb_violation_img.onload = () => {
    bulb_violation_image.value = bulb_violation_img;
    images_loaded.value++;
  };

  const cross_img = new Image();
  cross_img.src = "/assets/lightup/cross.svg";
  cross_img.onload = () => {
    cross_image.value = cross_img;
    images_loaded.value++;
  };

  // Document-level mouseup listener for drag
  document.addEventListener("mouseup", stop_drag);
});

onUnmounted(() => {
  document.removeEventListener("mouseup", stop_drag);
});

// Handle cell mousedown - start drag and emit first click
function on_cell_mousedown(coord: { row: number; col: number; zone: string }, event: MouseEvent) {
  if (coord.zone !== "game") return;

  // Start drag tracking
  is_dragging.value = true;
  drag_button.value = event.button;
  dragged_cells.value = new Set([`${coord.row},${coord.col}`]);

  emit("cell-click", coord.row, coord.col, event.button);
}

// Handle cell enter during drag - emit drag event for new cells
function on_cell_enter(coord: { row: number; col: number; zone: string }, _event: MouseEvent) {
  if (coord.zone !== "game") return;
  if (!is_dragging.value) return;

  const cell_key = `${coord.row},${coord.col}`;
  if (dragged_cells.value.has(cell_key)) return;

  dragged_cells.value.add(cell_key);
  emit("cell-drag", coord.row, coord.col);
}

// Handle mouseup anywhere - stop drag
function stop_drag() {
  is_dragging.value = false;
  dragged_cells.value.clear();
}

// Compute lit_cells from board if not provided (for preview/browser modes)
const computed_lit_cells = computed(() => {
  if (props.state.lit_cells) return props.state.lit_cells;
  const { rows, cols } = props.state.definition;
  return compute_lit_cells(props.state.board, rows, cols);
});

// Helper to check if a cell is lit
function is_cell_lit(row: number, col: number): boolean {
  const cols = props.state.definition.cols;
  const i = row * cols + col;
  return computed_lit_cells.value[i] || false;
}

// Lightup cell renderer
const cell_renderer = computed((): CellRenderer => {
  // Access for reactivity
  const _ = images_loaded.value;
  const current_theme = theme.value;
  const current_bulb = bulb_image.value;
  const current_bulb_violation = bulb_violation_image.value;
  const current_cross = cross_image.value;

  return (ctx, row, col, x, y, size, _state) => {
    const puzzle_state = props.state;
    const value = puzzle_state.board[row][col];
    const is_lit = is_cell_lit(row, col);

    // Determine background color
    let bg_color = current_theme.background;
    if (WALL_STATES.includes(value)) {
      bg_color = current_theme.wall;
    } else if (is_lit || value === LightupCell.BULB) {
      bg_color = current_theme.lit;
    }

    // Draw cell background
    ctx.fillStyle = bg_color;
    ctx.fillRect(x, y, size + 1, size + 1);

    // Render content based on cell type
    if (WALL_STATES.includes(value)) {
      // Wall cell with optional number
      const wall_number = NUMBERED_WALLS.includes(value) ? value : null;

      if (wall_number !== null) {
        // Check for violation
        const has_violation = puzzle_state.violations?.some(
          (v) =>
            v.rule_name === "numbered_wall_constraint_violated" &&
            v.locations?.some((loc) => loc.row === row && loc.col === col)
        );

        ctx.fillStyle = has_violation ? current_theme.error : current_theme.background;
        ctx.font = `${size * 0.7}px sans-serif`;
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(wall_number.toString(), x + size / 2 + 1, y + size / 2 + 1);
      }
    } else if (value === LightupCell.BULB) {
      // Bulb cell
      const has_violation = puzzle_state.violations?.some(
        (v) =>
          v.rule_name === "bulb_intersection_violation" &&
          v.locations?.some((loc) => loc.row === row && loc.col === col)
      );

      // Use the appropriate bulb image
      const bulb_img = has_violation ? current_bulb_violation : current_bulb;

      if (bulb_img) {
        ctx.drawImage(bulb_img, x, y, size, size);
      }
    } else if (value === LightupCell.CROSS) {
      // Cross mark
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
    // EMPTY cells: just background (already drawn with lit state)
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
    :outside-border-thickness="1"
    @cell-mousedown="on_cell_mousedown"
    @cell-enter="on_cell_enter"
  />
</template>
