<script setup lang="ts">
import FreeplayGameViewInstructionSlider from "@/features/freeplay/FreeplayGameViewInstructionSlider.vue";

import PuzzleMinesweeper from "@/features/games/minesweeper/minesweeper.puzzle.vue";
import type { PuzzleState } from "@/services/game/engines/types.ts";

const PUZZLE_SCALE = 1;

const board0: PuzzleState = {
  // @ts-expect-error intentionally partially defined
  definition: {
    rows: 7,
    cols: 7,
  },
  board: [
    [1, 0, 1, 2, 0, 0, 1],
    [0, 0, 0, 0, 0, 0, 0],
    [1, 0, 0, 3, 5, 0, 0],
    [0, 0, 1, 2, 0, 3, 1],
    [0, 0, 0, 0, 0, 4, 0],
    [0, 2, 0, 0, 0, 0, 1],
    [1, 1, 0, 0, 2, 0, 0],
  ],
  solved: false,
  immutable_cells: [],
  violations: [],
};

// Converting board1
const board1: Partial<PuzzleState> = {
  // @ts-expect-error intentionally partially defined
  definition: {
    rows: 7,
    cols: 7,
  },
  board: [
    [1, 11, 1, 2, 11, 11, 1],
    [9, 11, 11, 9, 9, 9, 11],
    [1, 0, 0, 3, 5, 0, 0],
    [0, 0, 1, 2, 0, 3, 1],
    [0, 0, 0, 0, 0, 4, 0],
    [9, 2, 11, 11, 9, 9, 1],
    [1, 1, 11, 11, 2, 11, 11],
  ],
};

// Converting board2
const board2: Partial<PuzzleState> = {
  // @ts-expect-error intentionally partially defined
  definition: {
    rows: 7,
    cols: 7,
  },
  board: [
    [1, 11, 1, 2, 11, 11, 1],
    [10, 11, 11, 10, 10, 10, 11],
    [1, 11, 11, 3, 5, 10, 11],
    [11, 11, 1, 2, 10, 3, 1],
    [11, 10, 11, 11, 10, 4, 11],
    [10, 2, 11, 11, 10, 10, 1],
    [1, 1, 11, 11, 2, 11, 11],
  ],
};
</script>

<template>
  <FreeplayGameViewInstructionSlider :num_pages="3">
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
        <div class="text-xl">Once all the cells have been filled it, try to submit to check your answer.</div>
        <PuzzleMinesweeper :scale="PUZZLE_SCALE" :state="board2" class="mx-auto" />
      </div>
    </template>
  </FreeplayGameViewInstructionSlider>
</template>
