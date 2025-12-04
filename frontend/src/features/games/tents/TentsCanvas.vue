<script setup lang="ts">
/**
 * TentsCanvas - Canvas-based renderer for Tents
 */
import { ref, computed, onMounted, onUnmounted } from "vue";
import CanvasBoard from "@/features/gameboard/canvas-board.vue";
import { useCanvasTheme } from "@/features/gameboard/canvas-theme";
import type { CellRenderer } from "@/features/gameboard/canvas-types";
import { TentsCell } from "./useTentsGame";
import type { TentsMeta, RuleViolation } from "@/core/games/types/puzzle-types.ts";

const props = defineProps<{
  state: {
    definition: { rows: number; cols: number; meta: TentsMeta };
    board: number[][];
    violations?: RuleViolation[];
  };
}>();

const emit = defineEmits<{
  (e: "cell-click", row: number, col: number, button: number): void;
  (e: "cell-drag", row: number, col: number): void;
}>();

const { theme } = useCanvasTheme();

const is_dragging = ref(false);
const drag_button = ref<number>(0);
const dragged_cells = ref<Set<string>>(new Set());

const images = ref<Record<string, HTMLImageElement | null>>({ tent: null, tree: null });
const images_loaded = ref(0);

onMounted(() => {
  const assets = { tent: "/assets/tents/tent.svg", tree: "/assets/tents/tree.svg" };
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
  if (coord.zone !== "game" || !is_dragging.value) return;
  const cell_key = `${coord.row},${coord.col}`;
  if (dragged_cells.value.has(cell_key)) return;
  dragged_cells.value.add(cell_key);
  emit("cell-drag", coord.row, coord.col);
}

function stop_drag() { is_dragging.value = false; dragged_cells.value.clear(); }

const cell_renderer = computed((): CellRenderer => {
  const _ = images_loaded.value;
  const current_theme = theme.value;
  const current_images = images.value;

  return (ctx, row, col, x, y, size, _state) => {
    const puzzle_state = props.state;

    // Top gutter: column tent counts
    if (row === 0) {
      const actual_col = col - 1;
      const col_count = puzzle_state.definition.meta.col_tent_counts[actual_col];
      const has_violation = puzzle_state.violations?.some(
        (v) => v.rule_name === "line_sum_col_exceeded" && v.locations?.some((loc) => loc.row === -1 && loc.col === actual_col)
      );
      ctx.fillStyle = has_violation ? current_theme.error : "black";
      ctx.font = `bold ${size * 0.7}px sans-serif`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(col_count.toString(), x + size / 2, y + size / 2);
      return;
    }

    // Left gutter: row tent counts
    if (col === 0) {
      const actual_row = row - 1;
      const row_count = puzzle_state.definition.meta.row_tent_counts[actual_row];
      const has_violation = puzzle_state.violations?.some(
        (v) => v.rule_name === "line_sum_row_exceeded" && v.locations?.some((loc) => loc.row === actual_row && loc.col === -1)
      );
      ctx.fillStyle = has_violation ? current_theme.error : "black";
      ctx.font = `bold ${size * 0.7}px sans-serif`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(row_count.toString(), x + size / 2, y + size / 2);
      return;
    }

    // Main grid
    const board_row = row - 1;
    const board_col = col - 1;
    const value = puzzle_state.board[board_row][board_col];

    const has_violation = puzzle_state.violations?.some(
      (v) => v.rule_name === "tents_intersecting" && v.locations?.some((loc) => loc.row === board_row && loc.col === board_col)
    );

    const green_bg = "#7bf1a8";
    const red_bg = "#fca5a5";

    if (value === TentsCell.TENT) {
      ctx.fillStyle = has_violation ? red_bg : green_bg;
      ctx.fillRect(x, y, size + 1, size + 1);
      if (current_images.tent) ctx.drawImage(current_images.tent, x, y, size, size);
    } else if (value === TentsCell.TREE) {
      ctx.fillStyle = green_bg;
      ctx.fillRect(x, y, size + 1, size + 1);
      if (current_images.tree) ctx.drawImage(current_images.tree, x, y, size, size);
    } else if (value === TentsCell.GREEN) {
      ctx.fillStyle = green_bg;
      ctx.fillRect(x, y, size + 1, size + 1);
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
    :gutter-top="1"
    :gutter-left="1"
    :gutter-top-inside-borders="'none'"
    :gutter-left-inside-borders="'none'"
    :draw-gutter-top-outside-border="false"
    :draw-gutter-left-outside-border="false"
    :outside-border-thickness="2"
    :inside-border-thickness="2"
    @cell-mousedown="on_cell_mousedown"
    @cell-enter="on_cell_enter"
  />
</template>
