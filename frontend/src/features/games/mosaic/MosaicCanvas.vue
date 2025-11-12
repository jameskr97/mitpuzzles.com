<script setup lang="ts">
/**
 * MosaicCanvas - Canvas-based renderer for Mosaic
 */
import { ref, computed, onMounted, onUnmounted } from "vue";
import CanvasBoard from "@/features/gameboard/canvas-board.vue";
import { useCanvasTheme } from "@/features/gameboard/canvas-theme";
import type { CellRenderer } from "@/features/gameboard/canvas-types";
import { MosaicCell } from "./useMosaicGame";
import type { RuleViolation } from "@/types/game-types";

const props = defineProps<{
  state: {
    definition: { rows: number; cols: number; initial_state?: number[][] };
    board: number[][];
    violations?: RuleViolation[];
  };
  get_number_clue?: (row: number, col: number) => number | null;
}>();

// Default get_number_clue reads from initial_state (values 0-9 are number clues)
function default_get_number_clue(row: number, col: number): number | null {
  const initial = props.state.definition.initial_state;
  if (!initial || !initial[row]) return null;
  const value = initial[row][col];
  // In mosaic, values 0-9 in initial_state are number clues
  return (value >= 0 && value <= 9) ? value : null;
}

const get_number_clue = computed(() => props.get_number_clue ?? default_get_number_clue);

const emit = defineEmits<{
  (e: "cell-click", row: number, col: number, button: number): void;
  (e: "cell-drag", row: number, col: number): void;
}>();

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
  if (coord.zone !== "game" || !is_dragging.value) return;
  const cell_key = `${coord.row},${coord.col}`;
  if (dragged_cells.value.has(cell_key)) return;
  dragged_cells.value.add(cell_key);
  emit("cell-drag", coord.row, coord.col);
}

function stop_drag() { is_dragging.value = false; dragged_cells.value.clear(); }

const cell_renderer = computed((): CellRenderer => {
  const current_theme = theme.value;

  return (ctx, row, col, x, y, size, _state) => {
    const puzzle_state = props.state;
    const value = puzzle_state.board[row][col];

    const has_violation = puzzle_state.violations?.some(
      (v) => v.rule_name === "mosaic_shaded_count_violation" && v.locations?.some((loc) => loc.row === row && loc.col === col)
    );

    let bg_color: string;
    let text_color: string;

    if (has_violation) {
      bg_color = "#fca5a5";
      text_color = "#000000";
    } else if (value === MosaicCell.SHADED) {
      bg_color = "#000000";
      text_color = "#ffffff";
    } else if (value === MosaicCell.CROSS) {
      bg_color = "#ffffff";
      text_color = "#000000";
    } else {
      bg_color = "#d1d5db";
      text_color = "#000000";
    }

    ctx.fillStyle = bg_color;
    ctx.fillRect(x + 1, y + 1, size, size);

    ctx.strokeStyle = "#9ca3af";
    ctx.lineWidth = 1;
    ctx.strokeRect(x, y, size, size);

    const number_clue = get_number_clue.value(row, col);
    if (number_clue !== null) {
      ctx.fillStyle = text_color;
      ctx.font = `bold ${size * 0.6}px sans-serif`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(number_clue.toString(), x + size / 2, y + size / 2);
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
    grid-color="#99a1af"
    outside-border-color="#99a1af"
    :inside-border-thickness="1"
    :outside-border-thickness="2"
    @cell-mousedown="on_cell_mousedown"
    @cell-enter="on_cell_enter"
  />
</template>
