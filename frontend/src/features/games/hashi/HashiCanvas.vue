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
import type { HashiBridge } from "@/services/game/engines/types";

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
      // Horizontal bridge
      const min_col = Math.min(c1, c2);
      const max_col = Math.max(c1, c2);
      for (let c = min_col; c <= max_col; c++) {
        const key = `${r1},${c}`;
        const existing = map.get(key) || { horizontal: 0, vertical: 0 };
        existing.horizontal = bridge.count;
        map.set(key, existing);
      }
    } else {
      // Vertical bridge
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

// Helper functions
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

  // Determine primary direction based on relative position
  const dy = current_row - src_row;
  const dx = current_col - src_col;
  let dr = 0, dc = 0;

  if (Math.abs(dx) > Math.abs(dy)) {
    dc = dx > 0 ? 1 : -1;
  } else if (Math.abs(dy) > Math.abs(dx)) {
    dr = dy > 0 ? 1 : -1;
  } else if (dx !== 0) {
    dc = dx > 0 ? 1 : -1;
  } else {
    drag_state.destination = null;
    return;
  }

  drag_state.destination = props.find_island_in_direction(src_row, src_col, dr, dc);
}

// Native event handlers
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

// Set up native event listeners
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

// Force redraw when drag state changes
watch(
  () => [drag_state.source, drag_state.destination, drag_state.dragging],
  () => {
    const board = canvas_board_ref.value as any;
    board?.redraw?.();
  },
  { deep: true }
);

// Cell renderer
const cell_renderer = computed((): CellRenderer => {
  const current_theme = theme.value;
  const current_bridges = cell_bridges.value;
  const current_islands = props.state.islands;
  const current_counts = props.state.island_bridge_counts;
  const current_drag = drag_state;
  const all_bridges = props.state.bridges;

  return (ctx, row, col, x, y, size) => {
    const key = `${row},${col}`;
    const island_count = current_islands.get(key);
    const bridge_info = current_bridges.get(key);
    const island_radius = size * ISLAND_RADIUS_RATIO;
    const center_x = x + size / 2;
    const center_y = y + size / 2;
    const is_drag_source = current_drag.source?.[0] === row && current_drag.source?.[1] === col;
    const is_drag_dest = current_drag.destination?.[0] === row && current_drag.destination?.[1] === col;

    // Background
    ctx.fillStyle = current_theme.background;
    ctx.fillRect(x, y, size + 1, size + 1);

    const is_island_cell = island_count !== undefined;

    // Draw bridges
    if (is_island_cell) {
      // For island cells, draw bridge segments from center outward
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
          // Horizontal bridge
          const to_right = other_col > col;
          if (count === 1) {
            ctx.beginPath();
            ctx.moveTo(center_x, center_y);
            ctx.lineTo(to_right ? x + size : x, center_y);
            ctx.stroke();
          } else {
            ctx.beginPath();
            ctx.moveTo(center_x, center_y - BRIDGE_GAP);
            ctx.lineTo(to_right ? x + size : x, center_y - BRIDGE_GAP);
            ctx.stroke();
            ctx.beginPath();
            ctx.moveTo(center_x, center_y + BRIDGE_GAP);
            ctx.lineTo(to_right ? x + size : x, center_y + BRIDGE_GAP);
            ctx.stroke();
          }
        } else {
          // Vertical bridge
          const to_down = other_row > row;
          if (count === 1) {
            ctx.beginPath();
            ctx.moveTo(center_x, center_y);
            ctx.lineTo(center_x, to_down ? y + size : y);
            ctx.stroke();
          } else {
            ctx.beginPath();
            ctx.moveTo(center_x - BRIDGE_GAP, center_y);
            ctx.lineTo(center_x - BRIDGE_GAP, to_down ? y + size : y);
            ctx.stroke();
            ctx.beginPath();
            ctx.moveTo(center_x + BRIDGE_GAP, center_y);
            ctx.lineTo(center_x + BRIDGE_GAP, to_down ? y + size : y);
            ctx.stroke();
          }
        }
      }
    } else if (bridge_info) {
      // For non-island cells, draw full line across cell
      ctx.strokeStyle = current_theme.text;
      ctx.lineWidth = BRIDGE_WIDTH;
      ctx.lineCap = "butt";

      if (bridge_info.horizontal > 0) {
        if (bridge_info.horizontal === 1) {
          ctx.beginPath();
          ctx.moveTo(x, center_y);
          ctx.lineTo(x + size, center_y);
          ctx.stroke();
        } else {
          ctx.beginPath();
          ctx.moveTo(x, center_y - BRIDGE_GAP);
          ctx.lineTo(x + size, center_y - BRIDGE_GAP);
          ctx.stroke();
          ctx.beginPath();
          ctx.moveTo(x, center_y + BRIDGE_GAP);
          ctx.lineTo(x + size, center_y + BRIDGE_GAP);
          ctx.stroke();
        }
      }
      if (bridge_info.vertical > 0) {
        if (bridge_info.vertical === 1) {
          ctx.beginPath();
          ctx.moveTo(center_x, y);
          ctx.lineTo(center_x, y + size);
          ctx.stroke();
        } else {
          ctx.beginPath();
          ctx.moveTo(center_x - BRIDGE_GAP, y);
          ctx.lineTo(center_x - BRIDGE_GAP, y + size);
          ctx.stroke();
          ctx.beginPath();
          ctx.moveTo(center_x + BRIDGE_GAP, y);
          ctx.lineTo(center_x + BRIDGE_GAP, y + size);
          ctx.stroke();
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
          ctx.beginPath();
          ctx.moveTo(x, center_y);
          ctx.lineTo(x + size, center_y);
          ctx.stroke();
        } else {
          ctx.beginPath();
          ctx.moveTo(center_x, y);
          ctx.lineTo(center_x, y + size);
          ctx.stroke();
        }
        ctx.globalAlpha = 1;
      }
    }

    // Draw islands
    if (island_count !== undefined) {
      const current_bridge_count = current_counts.get(key) || 0;
      const is_satisfied = current_bridge_count === island_count;

      ctx.beginPath();
      ctx.arc(center_x, center_y, island_radius, 0, Math.PI * 2);

      // Fill color based on state
      if (is_drag_source) {
        ctx.fillStyle = current_theme.selectFill || "#e0e7ff";
      } else if (is_drag_dest) {
        ctx.fillStyle = current_theme.targetFill || "#fef3c7";
      } else {
        ctx.fillStyle = current_theme.background;
      }
      ctx.fill();

      // Border color
      if (is_drag_source) {
        ctx.strokeStyle = current_theme.selectBorder || "#4f46e5";
        ctx.lineWidth = 3;
      } else if (is_drag_dest) {
        ctx.strokeStyle = current_theme.targetBorder || "#f59e0b";
        ctx.lineWidth = 3;
      } else if (is_satisfied) {
        ctx.strokeStyle = current_theme.hint;
        ctx.lineWidth = 3;
      } else {
        ctx.strokeStyle = current_theme.text;
        ctx.lineWidth = 2;
      }
      ctx.stroke();

      // Text color
      if (is_drag_source) {
        ctx.fillStyle = current_theme.selectBorder || "#4f46e5";
      } else if (is_drag_dest) {
        ctx.fillStyle = current_theme.targetBorder || "#f59e0b";
      } else if (is_satisfied) {
        ctx.fillStyle = current_theme.hint;
      } else {
        ctx.fillStyle = current_theme.text;
      }
      ctx.font = `bold ${size * 0.45}px sans-serif`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(island_count.toString(), center_x, center_y + 1);
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
