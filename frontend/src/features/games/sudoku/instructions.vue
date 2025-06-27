<script setup lang="ts">
import GameViewInstructionsSlider from "@/components/gameview.instructions.slider.vue";
import PuzzleSudoku from "@/features/games/sudoku/sudoku.puzzle.vue";
import { useRoute } from "vue-router";
import { useGameLayout } from "@/composables/useGameLayout.ts";
import { computed } from "vue";
import { ACTIVE_GAMES } from "@/constants.ts";
import type { PuzzleStateSudoku } from "@/services/states.ts";
import { getPersistentHighlightSudokuBoard } from "@/features/games/sudoku/getPersistentHighlightSudokuBoard.ts";

const route = useRoute();
const layout = useGameLayout();
const game_type = route.meta.game_type as string;
const game_type_capitalized = computed(() => game_type.charAt(0).toUpperCase() + game_type.slice(1));
const game_entry = ACTIVE_GAMES[game_type];

// @ts-expect-error ignore any missing fields
const board0: PuzzleStateSudoku = {
  cols: 4,
  rows: 4,
  board: [3, 4, 0, 0, 0, 0, 4, 0, 4, 0, 3, 2, 0, 3, 0, 4],
  board_initial: [3, 4, 0, 0, 0, 0, 4, 0, 4, 0, 3, 2, 0, 3, 0, 4],
};

const board0Solved: PuzzleStateSudoku = {
  cols: 4,
  rows: 4,
  board: [3, 4, 2, 1, 1, 2, 4, 3, 4, 1, 3, 2, 2, 3, 1, 4],
  board_initial: [3, 4, 0, 0, 0, 0, 4, 0, 4, 0, 3, 2, 0, 3, 0, 4],
  board: [3, 4, 2, 1, 1, 2, 4, 3, 4, 1, 3, 2, 2, 3, 1, 4],
};


const Board0Highlighted = getPersistentHighlightSudokuBoard({
  cell_class: "bg-red-400!",
  cells: [
    {row: 0, col: 2},
    {row: 0, col: 3},
    {row: 1, col: 0},
    {row: 1, col: 1},
    {row: 1, col: 3},
    {row: 2, col: 1},
    {row: 3, col: 0},
    {row: 3, col: 2},
  ]
})

</script>

<template>
  <GameViewInstructionsSlider :num_pages="3">
    <template #page1>
      <div class="flex flex-col gap-2 m-2 h-full text-center">
        <div class="text-xl mb-2">
          Sudoku is a logic puzzle played on a 9x9 grid. The grid is divided into 3x3 boxes, and some cells already
          contain numbers.
        </div>
        <PuzzleSudoku :scale="1" :state="board0" class="mx-auto" />
      </div>
    </template>

    <template #page2>
      <div class="flex flex-col gap-2 m-2 h-full text-center">
        <div class="text-xl mb-2">
          Your goal is to <span class="text-red-500">fill in the empty cells</span> with numbers from 1 to 9. Each row, column, and 3x3 box must contain
          <span class="text-red-500"></span> without repetition.
        </div>
        <Board0Highlighted :scale="1" :state="board0" class="mx-auto" />
      </div>
    </template>

    <template #page3>
      <div class="flex flex-col gap-2 m-2 h-full text-center">
        <div class="text-xl mb-2">
          The puzzle is solved when all cells are filled and every row, column, and 3×3 box contains the digits 1-9
          exactly once.
        </div>
        <Board0Highlighted :scale="1" :state="board0Solved" class="mx-auto" />
      </div>
    </template>
  </GameViewInstructionsSlider>
</template>
