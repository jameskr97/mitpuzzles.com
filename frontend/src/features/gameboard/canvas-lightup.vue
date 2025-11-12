<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import CanvasBoard from "./canvas-board.vue";
import { useCanvasTheme } from "./canvas-theme";
import type { PuzzleState, LightupMeta } from "@/services/game/engines/types";
import type { createPuzzleInteractionBridge } from "@/features/games.composables/setupPuzzleInteractionBridge";
import type { CellRenderer } from "./canvas-types";
import { LightupCell } from "@/services/game/engines/translator";

// Props
const props = defineProps<{
  state: PuzzleState<LightupMeta>;
  interact?: ReturnType<typeof createPuzzleInteractionBridge>;
}>();

const { theme } = useCanvasTheme();

// Preload images
const bulb_image = ref<HTMLImageElement | null>(null);
const bulb_violation_image = ref<HTMLImageElement | null>(null);
const cross_image = ref<HTMLImageElement | null>(null);

onMounted(() => {
  const bulb_img = new Image();
  bulb_img.src = "/assets/lightup/bulb.svg";
  bulb_img.onload = () => {
    bulb_image.value = bulb_img;
  };

  const bulb_violation_img = new Image();
  bulb_violation_img.src = "/assets/lightup/bulb-violation.svg";
  bulb_violation_img.onload = () => {
    bulb_violation_image.value = bulb_violation_img;
  };

  const cross_img = new Image();
  cross_img.src = "/assets/lightup/cross.svg";
  cross_img.onload = () => {
    cross_image.value = cross_img;
  };
});

// Wall states
const WALL_STATES = [
  LightupCell.WALL_0,
  LightupCell.WALL_1,
  LightupCell.WALL_2,
  LightupCell.WALL_3,
  LightupCell.WALL_4,
  LightupCell.WALL_NO_CONSTRAINT,
];

// Calculate which cells are lit by bulbs
const lit_cells = computed(() => {
  const rows = props.state.definition.rows;
  const cols = props.state.definition.cols;
  const board = props.state.board;
  const lit = new Array(rows * cols).fill(false);

  // Cardinal direction deltas
  const directions = [
    [-1, 0], // up
    [1, 0],  // down
    [0, -1], // left
    [0, 1],  // right
  ];

  // For each bulb, propagate light in all 4 directions
  for (let row = 0; row < rows; row++) {
    for (let col = 0; col < cols; col++) {
      if (board[row][col] !== LightupCell.BULB) continue;

      // Propagate light in each cardinal direction
      for (const [dy, dx] of directions) {
        let r = row + dy;
        let c = col + dx;

        // Continue until hitting a wall or boundary
        while (r >= 0 && r < rows && c >= 0 && c < cols) {
          const i = r * cols + c;

          // Stop if we hit a wall
          if (WALL_STATES.includes(board[r][c])) {
            break;
          }

          lit[i] = true;
          r += dy;
          c += dx;
        }
      }
    }
  }

  return lit;
});

// Helper to check if a cell is lit
function is_cell_lit(row: number, col: number): boolean {
  const cols = props.state.definition.cols;
  const i = row * cols + col;
  return lit_cells.value[i] || false;
}

// Lightup cell renderer
const cell_renderer = computed((): CellRenderer => {
  const current_theme = theme.value;
  const current_bulb = bulb_image.value;
  const current_bulb_violation = bulb_violation_image.value;
  const current_cross = cross_image.value;

  return (ctx, row, col, x, y, size, state) => {
    const puzzle_state = state as PuzzleState<LightupMeta>;
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
      const wall_number = value <= LightupCell.WALL_4 ? value : null;

      if (wall_number !== null) {
        // Check for violation
        const has_violation = puzzle_state.violations?.some(
          (v) =>
            v.rule_name === "numbered_wall_constraint_violated" &&
            v.locations?.some((loc) => loc.row === row && loc.col === col),
        );

        ctx.fillStyle = has_violation ? current_theme.error : current_theme.background;
        ctx.font = `${size * 0.7}px sans-serif`;
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(wall_number.toString(), (x + size / 2) + 1, (y + size / 2) + 1);
      }
    }
    else if (value === LightupCell.BULB) {
      // Bulb cell
      const has_violation = puzzle_state.violations?.some(
        (v) =>
          v.rule_name === "bulb_intersection_violation" &&
          v.locations?.some((loc) => loc.row === row && loc.col === col),
      );

      // Use the appropriate bulb image
      const bulb_img = has_violation ? current_bulb_violation : current_bulb;

      if (bulb_img) {
        ctx.drawImage(bulb_img, x, y, size, size);
      }
    }
    else if (value === LightupCell.CROSS) {
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
    :rows="state.definition.rows"
    :cols="state.definition.cols"
    :state="state"
    :interact="interact"
    :cell-renderer="cell_renderer"
    :gap="1"
    :outside-border-thickness="1"
  />
</template>
