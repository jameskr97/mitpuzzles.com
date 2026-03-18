<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from "vue";
import CanvasBoard from "@/features/gameboard/canvas-board.vue";
import { useCanvasTheme } from "@/features/gameboard/canvas-theme";
import type { CellRenderer } from "@/features/gameboard/canvas-types";
import { LightupCell, WALL_STATES, NUMBERED_WALLS, compute_lit_cells } from "./useLightupGame";
import type { RuleViolation } from "@/core/games/types/puzzle-types.ts";

const props = defineProps<{
  state: {
    definition: { rows: number; cols: number };
    board: number[][];
    violations?: RuleViolation[];
    lit_cells?: boolean[];
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
const canvas_board_ref = ref<InstanceType<typeof CanvasBoard> | null>(null);
const is_dragging = ref(false);
const drag_button = ref<number>(0);
const dragged_cells = ref<Set<string>>(new Set());

const bulb_image = ref<HTMLImageElement | null>(null);
const bulb_violation_image = ref<HTMLImageElement | null>(null);
const cross_image = ref<HTMLImageElement | null>(null);
const images_loaded = ref(0);

onMounted(() => {
  const assets: [string, typeof bulb_image][] = [
    ["/assets/lightup/bulb.svg", bulb_image],
    ["/assets/lightup/bulb-violation.svg", bulb_violation_image],
    ["/assets/lightup/cross.svg", cross_image],
  ];
  for (const [path, target] of assets) {
    const img = new Image();
    img.src = path;
    img.onload = () => { target.value = img; images_loaded.value++; };
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

const computed_lit_cells = computed(() => {
  if (props.state.lit_cells) return props.state.lit_cells;
  const { rows, cols } = props.state.definition;
  return compute_lit_cells(props.state.board, rows, cols);
});

function is_cell_lit(row: number, col: number): boolean {
  const cols = props.state.definition.cols;
  return computed_lit_cells.value[row * cols + col] || false;
}

const cell_renderer = computed((): CellRenderer => {
  // @ts-expect-error reactive dependency trigger
  const _ = images_loaded.value;
  const current_theme = theme.value;
  const current_bulb = bulb_image.value;
  const current_bulb_violation = bulb_violation_image.value;
  const current_cross = cross_image.value;

  return (r, cell, row, col, _state) => {
    const puzzle_state = props.state;
    const value = puzzle_state.board[row][col];
    const is_lit = is_cell_lit(row, col);

    // Background
    const is_wall = (WALL_STATES as readonly number[]).includes(value);
    let bg_color = current_theme.background;
    if (is_wall) bg_color = current_theme.wall;
    else if (is_lit || value === LightupCell.BULB) bg_color = current_theme.lit;

    r.fillCell(cell, bg_color, 1);

    // Wall with optional number
    if (is_wall) {
      const wall_number = (NUMBERED_WALLS as readonly number[]).includes(value) ? value : null;
      if (wall_number !== null) {
        const has_violation = puzzle_state.violations?.some(
          (v) => v.rule_name === "numbered_wall_constraint_violated" && v.locations?.some((loc) => loc.row === row && loc.col === col)
        );
        r.textCentered(cell, wall_number.toString(), { color: has_violation ? current_theme.error : current_theme.background, sizeFactor: 0.7, offsetY: 1 });
      }
    } else if (value === LightupCell.BULB) {
      const has_violation = puzzle_state.violations?.some(
        (v) => v.rule_name === "bulb_intersection_violation" && v.locations?.some((loc) => loc.row === row && loc.col === col)
      );
      const bulb_img = has_violation ? current_bulb_violation : current_bulb;
      if (bulb_img) r.imageCell(cell, bulb_img);
    } else if (value === LightupCell.CROSS) {
      r.crossMark(cell, current_cross, { lineColor: current_theme.text });
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
    :outside-border-thickness="1"
    @cell-mousedown="on_cell_mousedown"
    @cell-enter="on_cell_enter"
    @cell-leave="on_cell_leave"
    @board-leave="on_board_leave"
  />
</template>
