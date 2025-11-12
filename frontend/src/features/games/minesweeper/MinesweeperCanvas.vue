<script setup lang="ts">
/**
 * MinesweeperCanvas - Canvas-based renderer for Minesweeper
 *
 * Clean event-based interface - emits cell-click events.
 * No dependency on old interaction bridge.
 */
import { ref, computed, onMounted, onUnmounted } from "vue";
import CanvasBoard from "@/features/gameboard/canvas-board.vue";
import type { CellRenderer } from "@/features/gameboard/canvas-types";
import { MinesweeperCell } from "./useMinesweeperGame";
import type { RuleViolation } from "@/types/game-types";

// Props
const props = defineProps<{
  state: {
    definition: { rows: number; cols: number };
    board: number[][];
    violations?: RuleViolation[];
  };
}>();

// Events
const emit = defineEmits<{
  (e: "cell-click", row: number, col: number, button: number): void;
  (e: "cell-drag", row: number, col: number): void;
}>();

// Canvas board ref for interaction
const canvas_board_ref = ref<InstanceType<typeof CanvasBoard> | null>(null);

// Drag state for click-and-drag support
const is_dragging = ref(false);
const drag_button = ref<number>(0);
const dragged_cells = ref<Set<string>>(new Set());

// Preload images
const images = ref<Record<string, HTMLImageElement | null>>({
  unopened: null,
  unopened_highlighted: null,
  cell_empty: null,
  cell_violation: null,
  number_1: null,
  number_2: null,
  number_3: null,
  number_4: null,
  number_5: null,
  number_6: null,
  number_7: null,
  number_8: null,
  flag: null,
  safe: null,
  question_mark: null,
});

const images_loaded = ref(0);

onMounted(() => {
  const assets = {
    unopened: "/assets/minesweeper/unopened-square.svg",
    unopened_highlighted: "/assets/minesweeper/unopened-square-highlighted.svg",
    cell_empty: "/assets/minesweeper/cell-empty.svg",
    cell_violation: "/assets/minesweeper/cell-violation.svg",
    number_1: "/assets/minesweeper/number-1.svg",
    number_2: "/assets/minesweeper/number-2.svg",
    number_3: "/assets/minesweeper/number-3.svg",
    number_4: "/assets/minesweeper/number-4.svg",
    number_5: "/assets/minesweeper/number-5.svg",
    number_6: "/assets/minesweeper/number-6.svg",
    number_7: "/assets/minesweeper/number-7.svg",
    number_8: "/assets/minesweeper/number-8.svg",
    flag: "/assets/minesweeper/flag.svg",
    safe: "/assets/minesweeper/cell-safe.svg",
    question_mark: "/assets/minesweeper/question-mark.svg",
  };

  for (const [key, path] of Object.entries(assets)) {
    const img = new Image();
    img.src = path;
    img.onload = () => {
      images.value[key] = img;
      images_loaded.value++;
    };
  }
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

// Listen for mouseup on document to stop drag even when outside board
onMounted(() => {
  document.addEventListener("mouseup", stop_drag);
});

onUnmounted(() => {
  document.removeEventListener("mouseup", stop_drag);
});

// Cell renderer
const cell_renderer = computed((): CellRenderer => {
  // Access images_loaded for reactivity
  const _ = images_loaded.value;
  const current_images = images.value;

  return (ctx, row, col, x, y, size, _state) => {
    const value = props.state.board[row][col];

    // Check for violation
    const has_violation = props.state.violations?.some(
      (v) =>
        v.rule_name === "minesweeper_surrounding_flag_violation" &&
        v.locations?.some((loc) => loc.row === row && loc.col === col)
    );

    // Background based on cell type
    const needs_unopened_bg = [
      MinesweeperCell.SAFE,
      MinesweeperCell.FLAG,
      MinesweeperCell.QUESTION_MARK,
    ].includes(value);

    if (needs_unopened_bg) {
      if (current_images.unopened) {
        ctx.drawImage(current_images.unopened, x, y, size, size);
      }
    } else if (
      value === MinesweeperCell.UNMARKED ||
      value === MinesweeperCell.UNMARKED_HIGHLIGHTED
    ) {
      // Will be drawn below
    } else {
      const bg_img = has_violation
        ? current_images.cell_violation
        : current_images.cell_empty;
      if (bg_img) {
        ctx.drawImage(bg_img, x, y, size, size);
      }
    }

    // Foreground content
    if (value === MinesweeperCell.UNMARKED) {
      if (current_images.unopened) {
        ctx.drawImage(current_images.unopened, x, y, size, size);
      }
    } else if (value === MinesweeperCell.UNMARKED_HIGHLIGHTED) {
      if (current_images.unopened_highlighted) {
        ctx.drawImage(current_images.unopened_highlighted, x, y, size, size);
      }
    } else if (value >= MinesweeperCell.ONE && value <= MinesweeperCell.EIGHT) {
      const number_images = [
        null,
        current_images.number_1,
        current_images.number_2,
        current_images.number_3,
        current_images.number_4,
        current_images.number_5,
        current_images.number_6,
        current_images.number_7,
        current_images.number_8,
      ];

      const img = number_images[value];
      if (img) {
        const diff = 1.3;
        const offset = size - size / diff;
        ctx.drawImage(
          img,
          x + offset / 2,
          y + offset / 2,
          size / diff,
          size / diff
        );
      }
    } else if (value === MinesweeperCell.FLAG) {
      if (current_images.flag) {
        ctx.drawImage(current_images.flag, x, y, size, size);
      }
    } else if (value === MinesweeperCell.QUESTION_MARK) {
      if (current_images.question_mark) {
        ctx.drawImage(current_images.question_mark, x, y, size, size);
      }
    } else if (value === MinesweeperCell.SAFE) {
      if (current_images.safe) {
        const diff = 1.5;
        const offset = size - size / diff;
        ctx.drawImage(
          current_images.safe,
          x + offset / 2,
          y + offset / 2,
          size / diff,
          size / diff
        );
      }
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
    :outside-border-thickness="0"
    outside-border-color="#757575"
    :inside-border-thickness="0"
    grid-color="#757575"
    :gap="0"
    @cell-mousedown="on_cell_mousedown"
    @cell-enter="on_cell_enter"
  />
</template>
