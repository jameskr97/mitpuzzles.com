<script setup lang="ts">
import FreeplayGameViewInstructionSlider from "@/features/freeplay/FreeplayGameViewInstructionSlider.vue";
import PuzzleKakurasu from "@/features/games/kakurasu/kakurasu.puzzle.vue";
import type { KakurasuMeta, PuzzleDefinition } from "@/services/game/engines/types.ts";

const def: Partial<PuzzleDefinition<KakurasuMeta>> = {
  rows: 4,
  cols: 4,
  meta: {
    row_sums: [1, 3, 5, 7],
    col_sums: [2, 4, 6, 8],
  },
};

// @ts-expect-error ignore any missing fields
const board0: Partial<PuzzleState<KakurasuMeta>> = {
  definition: def,
  board: [
    [0, 0, 0, 0],
    [0, 0, 0, 0],
    [0, 0, 0, 0],
    [0, 0, 0, 0],
  ],
};

// @ts-expect-error ignore any missing fields
const board1: Partial<PuzzleState<KakurasuMeta>> = {
  definition: def,
  board: [
    [1, 0, 0, 0],
    [0, 1, 0, 0],
    [0, 0, 0, 0],
    [0, 0, 0, 0],
  ],
};

// @ts-expect-error ignore any missing fields
const board2: Partial<PuzzleState<KakurasuMeta>> = {
  definition: def,
  board: [
    [1, 0, 0, 0],
    [0, 1, 1, 0],
    [1, 0, 1, 0],
    [1, 1, 0, 1],
  ],
};
</script>

<template>
  <FreeplayGameViewInstructionSlider :num_pages="3">
    <template #page1>
      <div class="flex flex-col gap-2 m-2 h-full text-center">
        <div class="text-xl mb-2">
          Kakurasu is a logic puzzle played on a grid. Each row and column has a value (1, 2, 3...), and your goal is to
          fill cells to match the target sums.
        </div>
        <PuzzleKakurasu :scale="1" :state="board0" class="mx-auto" />
      </div>
    </template>

    <template #page2>
      <div class="flex flex-col gap-2 m-2 h-full text-center">
        <div class="text-xl mb-2">
          Click on cells to fill them in. When a cell is filled, add its row value and column value to their respective
          sums. Aim to match all target sums shown at the edges.
        </div>
        <PuzzleKakurasu :scale="1" :state="board1" class="mx-auto" />
      </div>
    </template>

    <template #page3>
      <div class="flex flex-col gap-2 m-2 h-full text-center">
        <div class="text-xl mb-2">
          The puzzle is solved when all filled cells add up to exactly the target sums for every row and column. Submit
          your answer when complete.
        </div>
        <PuzzleKakurasu :scale="1" :state="board2" class="mx-auto" />
      </div>
    </template>
  </FreeplayGameViewInstructionSlider>
</template>
