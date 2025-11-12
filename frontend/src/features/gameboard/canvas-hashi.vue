<script setup lang="ts">
import { computed, ref, reactive, onMounted, onBeforeUnmount, watch } from "vue";
import CanvasBoard from "./canvas-board.vue";
import { useCanvasTheme } from "./canvas-theme";
import type { PuzzleState, HashiMeta, HashiBridge } from "@/services/game/engines/types";
import type { createPuzzleInteractionBridge } from "@/features/games.composables/setupPuzzleInteractionBridge";
import type { CellRenderer } from "./canvas-types";

// Props
const props = defineProps<{
  state: PuzzleState<HashiMeta>;
  interact?: ReturnType<typeof createPuzzleInteractionBridge>;
}>();

const { theme } = useCanvasTheme();

// Ref to CanvasBoard
const canvas_board_ref = ref<InstanceType<typeof CanvasBoard> | null>(null);

// Drag state
const drag_state = reactive({
  source: null as [number, number] | null,
  destination: null as [number, number] | null,
  dragging: false,
  button: 0,
});

// Constants for rendering
const ISLAND_RADIUS_RATIO = 0.38;
const BRIDGE_GAP = 4;
const BRIDGE_WIDTH = 3;

// Get bridges from player state
const bridges = computed((): HashiBridge[] => {
  return props.state.definition.meta?.bridges || [];
});

// Pre-compute island positions
const island_map = computed(() => {
  const map = new Map<string, number>();
  const board = props.state.definition.initial_state;
  for (let row = 0; row < board.length; row++) {
    for (let col = 0; col < board[row].length; col++) {
      if (board[row][col] > 0) {
        map.set(`${row},${col}`, board[row][col]);
      }
    }
  }
  return map;
});

// Pre-compute bridge count per island
const island_bridge_counts = computed(() => {
  const counts = new Map<string, number>();
  for (const bridge of bridges.value) {
    const key1 = `${bridge.island1[0]},${bridge.island1[1]}`;
    const key2 = `${bridge.island2[0]},${bridge.island2[1]}`;
    counts.set(key1, (counts.get(key1) || 0) + bridge.count);
    counts.set(key2, (counts.get(key2) || 0) + bridge.count);
  }
  return counts;
});

// Pre-compute cell bridge segments
const cell_bridges = computed(() => {
  const map = new Map<string, { horizontal: number; vertical: number }>();
  for (const bridge of bridges.value) {
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

// Helper functions
function same_position(a: [number, number], b: [number, number]): boolean {
  return a[0] === b[0] && a[1] === b[1];
}

function is_island(row: number, col: number): boolean {
  return props.state.definition.initial_state[row]?.[col] > 0;
}

function find_island_in_direction(row: number, col: number, dr: number, dc: number): [number, number] | null {
  const board = props.state.definition.initial_state;
  const rows = props.state.definition.rows;
  const cols = props.state.definition.cols;
  let r = row + dr;
  let c = col + dc;
  while (r >= 0 && r < rows && c >= 0 && c < cols) {
    if (board[r][c] > 0) return [r, c];
    r += dr;
    c += dc;
  }
  return null;
}

function would_cross_bridge(island1: [number, number], island2: [number, number], direction: "horizontal" | "vertical"): boolean {
  const [r1, c1] = island1;
  const [r2, c2] = island2;
  for (const bridge of bridges.value) {
    const [br1, bc1] = bridge.island1;
    const [br2, bc2] = bridge.island2;
    const bridge_horizontal = br1 === br2;
    if ((direction === "horizontal") === bridge_horizontal) continue;
    if (direction === "horizontal") {
      const our_row = r1;
      const our_col_min = Math.min(c1, c2);
      const our_col_max = Math.max(c1, c2);
      const their_col = bc1;
      const their_row_min = Math.min(br1, br2);
      const their_row_max = Math.max(br1, br2);
      if (their_col > our_col_min && their_col < our_col_max && our_row > their_row_min && our_row < their_row_max) {
        return true;
      }
    } else {
      const our_col = c1;
      const our_row_min = Math.min(r1, r2);
      const our_row_max = Math.max(r1, r2);
      const their_row = br1;
      const their_col_min = Math.min(bc1, bc2);
      const their_col_max = Math.max(bc1, bc2);
      if (our_col > their_col_min && our_col < their_col_max && their_row > our_row_min && their_row < our_row_max) {
        return true;
      }
    }
  }
  return false;
}

function toggle_bridge(island1: [number, number], island2: [number, number], button: number): void {
  const direction: "horizontal" | "vertical" = island1[0] === island2[0] ? "horizontal" : "vertical";
  const current_bridges = [...bridges.value];
  const existing_index = current_bridges.findIndex(
    (b) => (same_position(b.island1, island1) && same_position(b.island2, island2)) ||
           (same_position(b.island1, island2) && same_position(b.island2, island1))
  );
  const existing = existing_index >= 0 ? current_bridges[existing_index] : null;
  const current_count = existing?.count || 0;
  let next_count = button === 2 ? (current_count === 0 ? 2 : current_count - 1) : (current_count + 1) % 3;
  if (next_count > 0 && current_count === 0 && would_cross_bridge(island1, island2, direction)) return;
  if (next_count === 0 && existing_index >= 0) {
    current_bridges.splice(existing_index, 1);
  } else if (next_count > 0) {
    if (existing_index >= 0) {
      current_bridges[existing_index].count = next_count;
    } else {
      current_bridges.push({ island1, island2, count: next_count });
    }
  }
  if (props.state.definition.meta) {
    props.state.definition.meta.bridges = current_bridges;
  }
}

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
  drag_state.destination = find_island_in_direction(src_row, src_col, dr, dc);
}

// Native event handlers
function handle_mousedown(event: MouseEvent): void {
  const canvas = (canvas_board_ref.value as any)?.$el?.querySelector?.('canvas') as HTMLCanvasElement | null;
  if (!canvas) return;
  const cell = get_cell_from_position(canvas, event.clientX, event.clientY);
  if (!cell) return;
  event.preventDefault();
  if (is_island(cell.row, cell.col)) {
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
  const canvas = (canvas_board_ref.value as any)?.$el?.querySelector?.('canvas') as HTMLCanvasElement | null;
  if (!canvas) return;
  const cell = get_cell_from_position(canvas, event.clientX, event.clientY);
  if (!cell) return;
  drag_state.dragging = true;
  update_drag_destination(cell.row, cell.col);
}

function handle_mouseup(event: MouseEvent): void {
  if (!drag_state.source) return;
  if (drag_state.dragging && drag_state.destination) {
    toggle_bridge(drag_state.source, drag_state.destination, drag_state.button);
  }
  cancel_drag();
}

function handle_contextmenu(event: MouseEvent): void {
  event.preventDefault();
}

// Set up native event listeners
onMounted(() => {
  const canvas = (canvas_board_ref.value as any)?.$el?.querySelector?.('canvas') as HTMLCanvasElement | null;
  if (canvas) {
    canvas.addEventListener('mousedown', handle_mousedown);
    canvas.addEventListener('mousemove', handle_mousemove);
    canvas.addEventListener('mouseup', handle_mouseup);
    canvas.addEventListener('contextmenu', handle_contextmenu);
  }
});

onBeforeUnmount(() => {
  const canvas = (canvas_board_ref.value as any)?.$el?.querySelector?.('canvas') as HTMLCanvasElement | null;
  if (canvas) {
    canvas.removeEventListener('mousedown', handle_mousedown);
    canvas.removeEventListener('mousemove', handle_mousemove);
    canvas.removeEventListener('mouseup', handle_mouseup);
    canvas.removeEventListener('contextmenu', handle_contextmenu);
  }
});

// Force redraw when drag state changes
watch(
  () => [drag_state.source, drag_state.destination, drag_state.dragging],
  () => {
    // Trigger redraw by calling CanvasBoard's exposed redraw method
    const board = canvas_board_ref.value as any;
    board?.redraw?.();
  },
  { deep: true }
);

// Cell renderer
const cell_renderer = computed((): CellRenderer => {
  const current_theme = theme.value;
  const current_bridges = cell_bridges.value;
  const current_islands = island_map.value;
  const current_counts = island_bridge_counts.value;
  const current_drag = drag_state;

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

    // Existing bridges
    const is_island_cell = island_count !== undefined;

    if (is_island_cell) {
      // For island cells, look up actual bridges and draw each with correct count
      ctx.strokeStyle = current_theme.text;
      ctx.lineWidth = BRIDGE_WIDTH;
      ctx.lineCap = "butt";

      for (const bridge of bridges.value) {
        const [r1, c1] = bridge.island1;
        const [r2, c2] = bridge.island2;

        // Check if this island is part of this bridge
        const is_endpoint1 = r1 === row && c1 === col;
        const is_endpoint2 = r2 === row && c2 === col;
        if (!is_endpoint1 && !is_endpoint2) continue;

        const other_row = is_endpoint1 ? r2 : r1;
        const other_col = is_endpoint1 ? c2 : c1;
        const count = bridge.count;

        // Determine direction
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
          ctx.beginPath(); ctx.moveTo(x, center_y); ctx.lineTo(x + size, center_y); ctx.stroke();
        } else {
          ctx.beginPath(); ctx.moveTo(x, center_y - BRIDGE_GAP); ctx.lineTo(x + size, center_y - BRIDGE_GAP); ctx.stroke();
          ctx.beginPath(); ctx.moveTo(x, center_y + BRIDGE_GAP); ctx.lineTo(x + size, center_y + BRIDGE_GAP); ctx.stroke();
        }
      }
      if (bridge_info.vertical > 0) {
        if (bridge_info.vertical === 1) {
          ctx.beginPath(); ctx.moveTo(center_x, y); ctx.lineTo(center_x, y + size); ctx.stroke();
        } else {
          ctx.beginPath(); ctx.moveTo(center_x - BRIDGE_GAP, y); ctx.lineTo(center_x - BRIDGE_GAP, y + size); ctx.stroke();
          ctx.beginPath(); ctx.moveTo(center_x + BRIDGE_GAP, y); ctx.lineTo(center_x + BRIDGE_GAP, y + size); ctx.stroke();
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
          ctx.beginPath(); ctx.moveTo(x, center_y); ctx.lineTo(x + size, center_y); ctx.stroke();
        } else {
          ctx.beginPath(); ctx.moveTo(center_x, y); ctx.lineTo(center_x, y + size); ctx.stroke();
        }
        ctx.globalAlpha = 1;
      }
    }

    // Islands
    if (island_count !== undefined) {
      const current_bridge_count = current_counts.get(key) || 0;
      const is_satisfied = current_bridge_count === island_count;

      ctx.beginPath();
      ctx.arc(center_x, center_y, island_radius, 0, Math.PI * 2);

      // Fill color based on state
      if (is_drag_source) {
        ctx.fillStyle = current_theme.selectFill;
      } else if (is_drag_dest) {
        ctx.fillStyle = current_theme.targetFill;
      } else {
        ctx.fillStyle = current_theme.background;
      }
      ctx.fill();

      // Border color
      if (is_drag_source) {
        ctx.strokeStyle = current_theme.selectBorder;
        ctx.lineWidth = 3;
      } else if (is_drag_dest) {
        ctx.strokeStyle = current_theme.targetBorder;
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
        ctx.fillStyle = current_theme.selectBorder;
      } else if (is_drag_dest) {
        ctx.fillStyle = current_theme.targetBorder;
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
