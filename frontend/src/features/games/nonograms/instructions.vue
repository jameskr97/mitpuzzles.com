<script setup lang="ts">
import FreeplayGameViewInstructionSlider from "@/features/freeplay/FreeplayGameViewInstructionSlider.vue";
import PuzzleNonograms from "@/features/games/nonograms/nonograms.puzzle.vue";
import type { NonogramMeta, PuzzleDefinition, PuzzleState } from "@/services/game/engines/types.ts";
import { Separator } from "@/components/ui/separator";
import FreeplayGameViewInstructionPage from "@/features/freeplay/FreeplayGameViewInstructionPage.vue";

// @ts-expect-error ignore any missing fields
const def: PuzzleDefinition<NonogramMeta> = {
  rows: 5,
  cols: 5,
  meta: {
    row_hints: [[3], [1], [1, 2], [1, 2], [1, 2]],
    col_hints: [[2], [1, 3], [1], [3], [3]],
  },
  board: [
    [0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0],
  ],
};

const boardEmpty: PuzzleState<NonogramMeta> = {
  definition: def,
  board: [
    [0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0],
  ],
};

const boardHighlight: Partial<PuzzleState<NonogramMeta>> = {
  definition: def,
  board: [
    [0, 0, 0, 0, 0],
    [1, 1, 1, 1, 0],
    [0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0],
  ],
};

// @ts-expect-error ignore any missing fields
const page2: Partial<PuzzleState<NonogramMeta>> = {
  definition: def,
  board: [
    [0, 1, 0, 0, 0],
    [0, 0, 0, 0, 0],
    [0, 1, 0, 0, 0],
    [0, 1, 0, 0, 0],
    [0, 1, 0, 0, 0],
  ],
};


// @ts-expect-error ignore any missing fields
const solution: Partial<PuzzleState<NonogramMeta>> = {
  definition: def,
  board: [
    [1, 1, 1, 0, 0],
    [1, 0, 0, 0, 0],
    [0, 1, 0, 1, 1],
    [0, 1, 0, 1, 1],
    [0, 1, 0, 1, 1],
  ],
};

// @ts-expect-error ignore any missing fields
const board2: Partial<PuzzleState<NonogramMeta>> = {
  definition: def,
  board: [
    [1, 0, 0, 0, 0],
    [0, 1, 1, 0, 0],
    [1, 0, 1, 0, 0],
    [1, 1, 0, 1, 0],
    [1, 1, 0, 1, 0],
  ],
};

const page3Left: Partial<PuzzleState<NonogramMeta>> = {
  definition: def,
  board: [
    [0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0],
    [0, 0, 0, 0, 1],
    [0, 0, 0, 0, 1],
    [0, 0, 0, 0, 1],
  ],
};

const page3Right: Partial<PuzzleState<NonogramMeta>> = {
  definition: def,
  board: [
    [0, 0, 0, 0, 1],
    [0, 0, 0, 0, 1],
    [0, 0, 0, 0, 1],
    [0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0],
  ],
};

const page4Right: Partial<PuzzleState<NonogramMeta>> = {
  definition: def,
  board: [
    [0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0],
    [0, 1, 0, 1, 1],
  ],
};

const page4Left: Partial<PuzzleState<NonogramMeta>> = {
  definition: def,
  board: [
    [0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0],
    [1, 0, 1, 1, 0],
  ],
};
</script>

<template>
  <FreeplayGameViewInstructionSlider :num_pages="5" slide-class="min-h-100">
    <template #page1>
      <FreeplayGameViewInstructionPage>
        <template #instruction>
          <p class="mb-2">
            Nonograms is a logic puzzle in which the goal is to place black cells <span class="inline-block h-5 w-5 bg-black rounded"></span>
            such that number constraints found on the edges of the board are satisfied.
          </p>
          <p>
            Below is an example board:
          </p>
        </template>
        <template #board>
          <PuzzleNonograms :scale="0.7" :state="page2" class="mx-auto" />
        </template>
      </FreeplayGameViewInstructionPage>
    </template>

    <template #page2>
      <FreeplayGameViewInstructionPage>
        <template #instruction>
          <p class="mb-2">
            To the left of each row and on top of each column are numbers that show the lengths of <span class="font-bold">runs of consecutive black squares</span> for that row/column.
          </p>
          <p>
            Your goal is to mark cells black <span class="inline-block h-5 w-5 bg-black rounded"></span> to create runs that match these numbers.
          </p>
        </template>
        <template #board>
          <PuzzleNonograms :scale="0.7" :state="boardEmpty" class="mx-auto" />
        </template>
      </FreeplayGameViewInstructionPage>
    </template>

    <template #page3>
      <FreeplayGameViewInstructionPage>
        <template #instruction>
          <p>
            For instance, in the example below, looking at the right column with hint “3”, each of the 2 shown placements satisfies the number clue since each consists of 3 consecutive black squares.
          </p>
        </template>
        <template #board>
          <div class="flex flex-row justify-between gap-2 text-center max-w-100 overflow-x-scroll">
            <div class="flex flex-col gap-2">
              <PuzzleNonograms :scale="0.5" :state="page3Left" class="mx-auto" />
            </div>
            <div class="flex flex-col gap-2">
              <PuzzleNonograms :scale="0.5" :state="page3Right" class="mx-auto" />
            </div>
          </div>
        </template>
      </FreeplayGameViewInstructionPage>
    </template>

    <template #page4>
      <FreeplayGameViewInstructionPage>
        <template #instruction>
          <div class="mb-2">
            Similarly, the bottom row with hints "1" and "2" can be satisfied in multiple ways - a single black cell, then at least one empty cell, then 2 consecutive black cells.
          </div>
          <div>
            Note that when there are <span class="font-bold"> multiple runs</span> in the same row/column, they must be separated by at least one empty cell.
          </div>
        </template>
        <template #board>
          <div class="flex flex-row justify-between gap-2 text-center">
            <div class="flex flex-col gap-2">
              <PuzzleNonograms :scale="0.5" :state="page4Left" class="mx-auto" />
            </div>
            <div class="flex flex-col gap-2">
              <PuzzleNonograms :scale="0.5" :state="page4Right" class="mx-auto" />
            </div>
          </div>
        </template>
      </FreeplayGameViewInstructionPage>
    </template>

    <template #page5>
      <FreeplayGameViewInstructionPage>
        <template #instruction>
          <p class="mb-2">
            The correct solution will uniquely satisfy the runs specified by all rows and column hints simultaneously
          </p>
          <p>
            Below is a full solved game board:
          </p>
        </template>
        <template #board>
          <PuzzleNonograms :scale="0.7" :state="solution" class="mx-auto" />
        </template>
      </FreeplayGameViewInstructionPage>

      <div class="flex flex-col gap-2"></div>
    </template>

    <template #controls>
      <div>Left click to cycle forward, right click to cycle backward between:</div>
      <ul class="list-decimal gap-2 h-full w-full ml-8">
        <li>Placing a box <i class="md-cell bg-black"></i></li>
        <li>Placing a cross <i class="md-cell md-cell-kakurasu-cross"></i></li>
        <li>Clearing the cell</li>
      </ul>
    </template>
  </FreeplayGameViewInstructionSlider>
</template>
