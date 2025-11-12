<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import CanvasBoard from "./canvas-board.vue";
import { useCanvasTheme } from "./canvas-theme";
import type { PuzzleState, MinesweeperMeta } from "@/services/game/engines/types";
import type { createPuzzleInteractionBridge } from "@/features/games.composables/setupPuzzleInteractionBridge";
import type { CellRenderer } from "./canvas-types";
import { MinesweeperCell } from "@/services/game/engines/translator";

// Props
const props = defineProps<{
  state: PuzzleState<MinesweeperMeta>;
  interact?: ReturnType<typeof createPuzzleInteractionBridge>;
}>();

const { theme } = useCanvasTheme();

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

// Track when images are loaded to trigger re-render
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

// Minesweeper cell renderer
const cell_renderer = computed((): CellRenderer => {
  // Access images_loaded to create reactive dependency
  const _ = images_loaded.value;
  const current_images = images.value;

  return (ctx, row, col, x, y, size, state) => {
    const puzzle_state = state as PuzzleState<MinesweeperMeta>;
    const value = puzzle_state.board[row][col];

    // Check for violation on this cell
    const has_violation = puzzle_state.violations?.some(
      (v) =>
        v.rule_name === "minesweeper_surrounding_flag_violation" &&
        v.locations?.some((loc) => loc.row === row && loc.col === col),
    );

    // Determine background based on cell type
    const needs_unopened_bg = [MinesweeperCell.SAFE, MinesweeperCell.FLAG, MinesweeperCell.QUESTION_MARK].includes(value);

    // Draw background
    if (needs_unopened_bg) {
      // For SAFE, FLAG, QUESTION_MARK: draw unopened square as background
      if (current_images.unopened) {
        ctx.drawImage(current_images.unopened, x, y, size, size);
      }
    }
    else if (value === MinesweeperCell.UNMARKED || value === MinesweeperCell.UNMARKED_HIGHLIGHTED) {
      // For UNMARKED: the image IS the cell (no separate background)
      // Will be drawn below
    }
    else {
      // For numbered cells and EMPTY: draw cell-empty or cell-violation as background
      const bg_img = has_violation ? current_images.cell_violation : current_images.cell_empty;
      if (bg_img) {
        ctx.drawImage(bg_img, x, y, size, size);
      }
    }

    // Draw foreground content
    if (value === MinesweeperCell.UNMARKED) {
      if (current_images.unopened) {
        ctx.drawImage(current_images.unopened, x, y, size, size);
      }
    }
    else if (value === MinesweeperCell.UNMARKED_HIGHLIGHTED) {
      if (current_images.unopened_highlighted) {
        ctx.drawImage(current_images.unopened_highlighted, x, y, size, size);
      }
    }
    else if (value >= MinesweeperCell.ONE && value <= MinesweeperCell.EIGHT) {
      // Draw numbered cells
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
        const offset = size - (size / diff);
        ctx.drawImage(img, x + offset / 2, y + offset / 2, size / diff, size / diff);
      }
    }
    else if (value === MinesweeperCell.FLAG) {
      if (current_images.flag) {
        ctx.drawImage(current_images.flag, x, y, size, size);
      }
    }
    else if (value === MinesweeperCell.QUESTION_MARK) {
      if (current_images.question_mark) {
        ctx.drawImage(current_images.question_mark, x, y, size, size);
      }
    }
    else if (value === MinesweeperCell.SAFE) {
      if (current_images.safe) {
        const diff = 1.5;
        const offset = size - (size / diff);
        ctx.drawImage(current_images.safe, x + offset / 2, y + offset / 2, size / diff, size / diff);
      }
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
    :outside-border-thickness="0"
    outside-border-color="#757575"
    :inside-border-thickness="0"
    grid-color="#757575"
    :gap="0"
  />
</template>
