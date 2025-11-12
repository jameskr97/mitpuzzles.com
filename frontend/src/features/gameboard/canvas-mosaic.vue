<script setup lang="ts">
import { computed } from "vue";
import CanvasBoard from "./canvas-board.vue";
import { useCanvasTheme } from "./canvas-theme";
import type { PuzzleState, MosaicMeta } from "@/services/game/engines/types";
import type { createPuzzleInteractionBridge } from "@/features/games.composables/setupPuzzleInteractionBridge";
import type { CellRenderer } from "./canvas-types";
import { MosaicCell } from "@/services/game/engines/translator";

// Props
const props = defineProps<{
  state: PuzzleState<MosaicMeta>;
  interact?: ReturnType<typeof createPuzzleInteractionBridge>;
}>();

const { theme } = useCanvasTheme();

// Helper to get the number clue from initial_state (if any)
function get_number_clue(row: number, col: number): number | null {
  const initial_value = props.state.definition.initial_state?.[row]?.[col];
  if (initial_value !== undefined && initial_value >= 0 && initial_value <= 9) {
    return initial_value;
  }
  return null;
}

// Mosaic cell renderer
const cell_renderer = computed((): CellRenderer => {
  const current_theme = theme.value;

  return (ctx, row, col, x, y, size, state) => {
    const puzzle_state = state as PuzzleState<MosaicMeta>;
    const value = puzzle_state.board[row][col];

    // Check for violation on this cell
    const has_violation = puzzle_state.violations?.some(
      (v) =>
        v.rule_name === "mosaic_shaded_count_violation" &&
        v.locations?.some((loc) => loc.row === row && loc.col === col),
    );

    // Determine background color based on cell state
    let bg_color: string;
    let text_color: string;

    if (has_violation) {
      // Violation: red background
      bg_color = "#fca5a5"; // red-300
      text_color = "#000000";
    }
    else if (value === MosaicCell.SHADED) {
      // Shaded: black background, white text
      bg_color = "#000000";
      text_color = "#ffffff";
    }
    else if (value === MosaicCell.CROSS) {
      // Cross: white background, black text
      bg_color = "#ffffff";
      text_color = "#000000";
    }
    else {
      // Unmarked: gray background, black text
      bg_color = "#d1d5db"; // gray-300
      text_color = "#000000";
    }

    // Draw cell background
    ctx.fillStyle = bg_color;
    ctx.fillRect(x + 1, y + 1, size, size);

    // Draw cell border (gray-400)
    ctx.strokeStyle = "#9ca3af"; // gray-400
    ctx.lineWidth = 1;
    ctx.strokeRect(x, y, size, size);

    // Draw number clue if present in initial_state
    const number_clue = get_number_clue(row, col);
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
    :interact="interact"
    :cell-renderer="cell_renderer"
    :gap="1"
    grid-color="#99a1af"
    outside-border-color="#99a1af"
    :inside-border-thickness="1"
    :outside-border-thickness="2"
  />
</template>
