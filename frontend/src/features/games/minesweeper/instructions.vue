<script setup lang="ts">
import GameViewInstructionsSlider from "@/components/gameview.instructions.slider.vue";

import PuzzleMinesweeper from "@/features/games/minesweeper/minesweeper.puzzle.vue";
import type { PuzzleStateMinesweeper } from "@/services/states.ts";

const PUZZLE_SCALE = 1;

// @ts-expect-error ignore any missing fields
const board0: PuzzleStateMinesweeper = {
  cols: 7,
  rows: 7,
  board: [1, 9, 1, 2, 9, 9, 1, 9, 9, 9, 9, 9, 9, 9, 1, 9, 9, 3, 5, 9, 9, 9, 9, 1, 2, 9, 3, 1, 9, 9, 9, 9, 9, 4, 9, 9, 2, 9, 9, 9, 9, 1, 1, 1, 9, 9, 2, 9, 9],
};

// @ts-expect-error ignore any missing fields
const board1: PuzzleStateMinesweeper = {
  cols: 7,
  rows: 7,
  board: [1, 11, 1, 2, 11, 11, 1, 10, 11, 11, 10, 10, 10, 11, 1, 9, 9, 3, 5, 9, 9, 9, 9, 1, 2, 9, 3, 1, 9, 9, 9, 9, 9, 4, 9, 10, 2, 11, 11, 10, 10, 1, 1, 1, 11, 11, 2, 11, 11],
};

// @ts-expect-error ignore any missing fields
const board2: PuzzleStateMinesweeper = {
  cols: 7,
  rows: 7,
  board: [1, 11, 1, 2, 11, 11, 1, 10, 11, 11, 10, 10, 10, 11, 1, 11, 11, 3, 5, 10, 11, 11, 11, 1, 2, 10, 3, 1, 11, 10, 11, 11, 10, 4, 11, 10, 2, 11, 11, 10, 10, 1, 1, 1, 11, 11, 2, 11, 11],
};


</script>

<template>
  <GameViewInstructionsSlider :num_pages="3">
    <template #page1>
      <div class="flex flex-col gap-2 m-2 h-full text-center">
        <div class="text-xl">
          Your goal is to deduce the location of all the bombs. To help you, all the numbers have been revealed.
        </div>
        <PuzzleMinesweeper :scale="PUZZLE_SCALE" :state="board0" class="mx-auto" />
      </div>
    </template>

    <template #page2>
      <div class="flex flex-col gap-2 m-2 h-full text-center">
        <div class="text-xl">
          Click on the empty cells <i class="md-cell md-cell-unrevealed"></i>, to change them to be
          <i class="md-cell w-full md-cell-empty inline-block mt-[2px]"></i> or flagged
          <i class="md-cell md-cell-flag"></i>.
        </div>
        <PuzzleMinesweeper :scale="PUZZLE_SCALE" :state="board1" class="mx-auto" />
      </div>
    </template>

    <template #page3>
      <div class="flex flex-col gap-2 m-2 h-full text-center">
        <div class="text-xl">
          Once all the cells have been filled it, try to submit to check your answer.
        </div>
        <PuzzleMinesweeper :scale="PUZZLE_SCALE" :state="board2" class="mx-auto" />
      </div>
    </template>
  </GameViewInstructionsSlider>
</template>

