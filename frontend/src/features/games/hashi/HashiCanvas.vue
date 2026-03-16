<script setup lang="ts">
/**
 * HashiCanvas - Canvas-based renderer for Hashi (Bridges)
 *
 * Drag-based interaction: drag from one island to another to add/toggle bridges.
 * Left drag = add bridge (0 → 1 → 2 → 0)
 * Right drag = remove bridge (2 → 1 → 0)
 */
import { ref, computed, reactive, onMounted, onUnmounted, watch } from "vue";
import CanvasBoard from "@/features/gameboard/canvas-board.vue";
import { useCanvasTheme } from "@/features/gameboard/canvas-theme";
import type { CellRenderer } from "@/features/gameboard/canvas-types";
import type { HashiBridge } from "@/core/games/types/puzzle-types.ts";

const props = defineProps<{
  state: {
    definition: { rows: number; cols: number; initial_state: number[][] };
    bridges: HashiBridge[];
    islands: Map<string, number>;
    island_bridge_counts: Map<string, number>;
  };
  is_island: (row: number, col: number) => boolean;
  find_island_in_direction: (row: number, col: number, dr: number, dc: number) => [number, number] | null;
}>();

const emit = defineEmits<{
  (e: "bridge-toggle", island1: [number, number], island2: [number, number], button: number): void;
}>();

const { theme } = useCanvasTheme();

const canvas_board_ref = ref<InstanceType<typeof CanvasBoard> | null>(null);
const drag_state = reactive({
  source: null as [number, number] | null,
  destination: null as [number, number] | null,
  dragging: false,
  button: 0,
});

// Rendering constants
const ISLAND_RADIUS_RATIO = 0.38;
const BRIDGE_GAP = 4;
const BRIDGE_WIDTH = 3;

// Pre-compute cell bridge segments for rendering
const cell_bridges = computed(() => {
  const map = new Map<string, { horizontal: number; vertical: number }>();
  for (const bridge of props.state.bridges) {
    const [r1, c1] = bridge.island1;
    const [r2, c2] = bridge.island2;
    if (r1 === r2) {
      const min_col = Math.min(c1, c2);
      const max_col = Math.max(c1, c2);
      for (let c = min_col; c <= max_col; c++) {
        const key = `${r1},${c}`;
        const existing = map.get(key) || { horizontal: 0, vertical: 0 };
        existing.horizontal = bridge.count;
        map.set(key, existing);
      }
    } else {
      const min_row = Math.min(r1, r2);
      const max_row = Math.max(r1, r2);
      for (let r = min_row; r <= max_row; r++) {
        const key = `${r},${c1}`;
        const existing = map.get(key) || { horizontal: 0, vertical: 0 };
        existing.vertical = bridge.count;
        map.set(key, existing);
      }
    }
  }
  return map;
});

function cancel_drag(): void {
  drag_state.source = null;
  drag_state.destination = null;
  drag_state.dragging = false;
}

function get_cell_from_position(canvas: HTMLCanvasElement, clientX: number, clientY: number): { row: number; col: number } | null {
  const rect = canvas.getBoundingClientRect();
  const x = clientX - rect.left;
  const y = clientY - rect.top;
  const rows = props.state.definition.rows;
  const cols = props.state.definition.cols;
  const cell_size = Math.min(rect.width / cols, rect.height / rows);
  const col = Math.floor(x / cell_size);
  const row = Math.floor(y / cell_size);
  if (row < 0 || row >= rows || col < 0 || col >= cols) return null;
  return { row, col };
}

function update_drag_destination(current_row: number, current_col: number): void {
  if (!drag_state.source) return;
  const [src_row, src_col] = drag_state.source;

  if (current_row === src_row && current_col === src_col) {
    drag_state.destination = null;
    return;
  }

  const dy = current_row - src_row;
  const dx = current_col - src_col;
  let dr = 0, dc = 0;

  if (Math.abs(dx) > Math.abs(dy)) dc = dx > 0 ? 1 : -1;
  else if (Math.abs(dy) > Math.abs(dx)) dr = dy > 0 ? 1 : -1;
  else if (dx !== 0) dc = dx > 0 ? 1 : -1;
  else { drag_state.destination = null; return; }

  drag_state.destination = props.find_island_in_direction(src_row, src_col, dr, dc);
}

function handle_mousedown(event: MouseEvent): void {
  const canvas = (canvas_board_ref.value as any)?.$el?.querySelector?.("canvas") as HTMLCanvasElement | null;
  if (!canvas) return;
  const cell = get_cell_from_position(canvas, event.clientX, event.clientY);
  if (!cell) return;
  event.preventDefault();

  if (props.is_island(cell.row, cell.col)) {
    drag_state.source = [cell.row, cell.col];
    drag_state.destination = null;
    drag_state.dragging = false;
    drag_state.button = event.button;
  } else {
    cancel_drag();
  }
}

function handle_mousemove(event: MouseEvent): void {
  if (!drag_state.source) return;
  const canvas = (canvas_board_ref.value as any)?.$el?.querySelector?.("canvas") as HTMLCanvasElement | null;
  if (!canvas) return;
  const cell = get_cell_from_position(canvas, event.clientX, event.clientY);
  if (!cell) return;
  drag_state.dragging = true;
  update_drag_destination(cell.row, cell.col);
}

function handle_mouseup(_event: MouseEvent): void {
  if (!drag_state.source) return;
  if (drag_state.dragging && drag_state.destination) {
    emit("bridge-toggle", drag_state.source, drag_state.destination, drag_state.button);
  }
  cancel_drag();
}

function handle_contextmenu(event: MouseEvent): void {
  event.preventDefault();
}

onMounted(() => {
  const canvas = (canvas_board_ref.value as any)?.$el?.querySelector?.("canvas") as HTMLCanvasElement | null;
  if (canvas) {
    canvas.addEventListener("mousedown", handle_mousedown);
    canvas.addEventListener("mousemove", handle_mousemove);
    canvas.addEventListener("mouseup", handle_mouseup);
    canvas.addEventListener("contextmenu", handle_contextmenu);
  }
  document.addEventListener("mouseup", handle_mouseup);
});

onUnmounted(() => {
  const canvas = (canvas_board_ref.value as any)?.$el?.querySelector?.("canvas") as HTMLCanvasElement | null;
  if (canvas) {
    canvas.removeEventListener("mousedown", handle_mousedown);
    canvas.removeEventListener("mousemove", handle_mousemove);
    canvas.removeEventListener("mouseup", handle_mouseup);
    canvas.removeEventListener("contextmenu", handle_contextmenu);
  }
  document.removeEventListener("mouseup", handle_mouseup);
});

watch(
  () => [drag_state.source, drag_state.destination, drag_state.dragging],
  () => { (canvas_board_ref.value as any)?.redraw?.(); },
  { deep: true }
);

// Helper to draw a line segment via raw ctx
function draw_bridge_line(ctx: CanvasRenderingContext2D, x1: number, y1: number, x2: number, y2: number) {
  ctx.beginPath();
  ctx.moveTo(x1, y1);
  ctx.lineTo(x2, y2);
  ctx.stroke();
}

const cell_renderer = computed((): CellRenderer => {
  const current_theme = theme.value;
  const current_bridges = cell_bridges.value;
  const current_islands = props.state.islands;
  const current_counts = props.state.island_bridge_counts;
  const current_drag = drag_state;
  const all_bridges = props.state.bridges;

  return (r, cell, row, col, _state) => {
    const ctx = r.ctx;
    const key = `${row},${col}`;
    const island_count = current_islands.get(key);
    const bridge_info = current_bridges.get(key);
    const island_radius = cell.size * ISLAND_RADIUS_RATIO;
    const { x, y, size, cx, cy } = cell;
    const is_drag_source = current_drag.source?.[0] === row && current_drag.source?.[1] === col;
    const is_drag_dest = current_drag.destination?.[0] === row && current_drag.destination?.[1] === col;

    r.fillCell(cell, current_theme.background, 1);

    const is_island_cell = island_count !== undefined;

    // Draw bridges
    if (is_island_cell) {
      ctx.strokeStyle = current_theme.text;
      ctx.lineWidth = BRIDGE_WIDTH;
      ctx.lineCap = "butt";

      for (const bridge of all_bridges) {
        const [r1, c1] = bridge.island1;
        const [r2, c2] = bridge.island2;

        const is_endpoint1 = r1 === row && c1 === col;
        const is_endpoint2 = r2 === row && c2 === col;
        if (!is_endpoint1 && !is_endpoint2) continue;

        const other_row = is_endpoint1 ? r2 : r1;
        const other_col = is_endpoint1 ? c2 : c1;
        const count = bridge.count;

        if (other_row === row) {
          const edge_x = other_col > col ? x + size : x;
          if (count === 1) {
            draw_bridge_line(ctx, cx, cy, edge_x, cy);
          } else {
            draw_bridge_line(ctx, cx, cy - BRIDGE_GAP, edge_x, cy - BRIDGE_GAP);
            draw_bridge_line(ctx, cx, cy + BRIDGE_GAP, edge_x, cy + BRIDGE_GAP);
          }
        } else {
          const edge_y = other_row > row ? y + size : y;
          if (count === 1) {
            draw_bridge_line(ctx, cx, cy, cx, edge_y);
          } else {
            draw_bridge_line(ctx, cx - BRIDGE_GAP, cy, cx - BRIDGE_GAP, edge_y);
            draw_bridge_line(ctx, cx + BRIDGE_GAP, cy, cx + BRIDGE_GAP, edge_y);
          }
        }
      }
    } else if (bridge_info) {
      ctx.strokeStyle = current_theme.text;
      ctx.lineWidth = BRIDGE_WIDTH;
      ctx.lineCap = "butt";

      if (bridge_info.horizontal > 0) {
        if (bridge_info.horizontal === 1) {
          draw_bridge_line(ctx, x, cy, x + size, cy);
        } else {
          draw_bridge_line(ctx, x, cy - BRIDGE_GAP, x + size, cy - BRIDGE_GAP);
          draw_bridge_line(ctx, x, cy + BRIDGE_GAP, x + size, cy + BRIDGE_GAP);
        }
      }
      if (bridge_info.vertical > 0) {
        if (bridge_info.vertical === 1) {
          draw_bridge_line(ctx, cx, y, cx, y + size);
        } else {
          draw_bridge_line(ctx, cx - BRIDGE_GAP, y, cx - BRIDGE_GAP, y + size);
          draw_bridge_line(ctx, cx + BRIDGE_GAP, y, cx + BRIDGE_GAP, y + size);
        }
      }
    }

    // Drag preview
    if (current_drag.dragging && current_drag.source && current_drag.destination && !island_count) {
      const [src_row, src_col] = current_drag.source;
      const [dst_row, dst_col] = current_drag.destination;
      let on_path = false;

      if (src_row === dst_row && src_row === row) {
        on_path = col >= Math.min(src_col, dst_col) && col <= Math.max(src_col, dst_col);
      } else if (src_col === dst_col && src_col === col) {
        on_path = row >= Math.min(src_row, dst_row) && row <= Math.max(src_row, dst_row);
      }

      if (on_path) {
        ctx.strokeStyle = current_theme.hint;
        ctx.lineWidth = BRIDGE_WIDTH;
        ctx.globalAlpha = 0.5;
        if (src_row === dst_row) {
          draw_bridge_line(ctx, x, cy, x + size, cy);
        } else {
          draw_bridge_line(ctx, cx, y, cx, y + size);
        }
        ctx.globalAlpha = 1;
      }
    }

    // Draw islands
    if (island_count !== undefined) {
      const current_bridge_count = current_counts.get(key) || 0;
      const is_satisfied = current_bridge_count === island_count;

      ctx.beginPath();
      ctx.arc(cx, cy, island_radius, 0, Math.PI * 2);

      if (is_drag_source) ctx.fillStyle = current_theme.selectFill || "#e0e7ff";
      else if (is_drag_dest) ctx.fillStyle = current_theme.targetFill || "#fef3c7";
      else ctx.fillStyle = current_theme.background;
      ctx.fill();

      if (is_drag_source) { ctx.strokeStyle = current_theme.selectBorder || "#4f46e5"; ctx.lineWidth = 3; }
      else if (is_drag_dest) { ctx.strokeStyle = current_theme.targetBorder || "#f59e0b"; ctx.lineWidth = 3; }
      else if (is_satisfied) { ctx.strokeStyle = current_theme.hint; ctx.lineWidth = 3; }
      else { ctx.strokeStyle = current_theme.text; ctx.lineWidth = 2; }
      ctx.stroke();

      let text_color: string;
      if (is_drag_source) text_color = current_theme.selectBorder || "#4f46e5";
      else if (is_drag_dest) text_color = current_theme.targetBorder || "#f59e0b";
      else if (is_satisfied) text_color = current_theme.hint;
      else text_color = current_theme.text;

      r.textCentered(cell, island_count.toString(), { color: text_color, sizeFactor: 0.45, offsetY: 1 });
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
    :outside-border-thickness="1"
    :inside-border-thickness="0"
    outside-border-color="#fff"
    grid-color="transparent"
  />
</template>
