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
          <div class="mb-2">
            Nonograms is a logic puzzle played on a grid where you mark cells black to meet specific requirements.
          </div>
        </template>
        <template #board>
          <PuzzleNonograms :scale="1" :state="boardEmpty" class="mx-auto" />
        </template>
      </FreeplayGameViewInstructionPage>
    </template>

    <template #page2>
      <FreeplayGameViewInstructionPage>
        <template #instruction>
          <div class="flex flex-col gap-2">
            <div>
              Cells can either be empty, black <span class="inline-block h-5 w-5 bg-black rounded"></span>, or crossed
              out <i class="md-cell md-cell-kakurasu-cross"></i>.
            </div>
            <Separator />

            <ul class="list-disc list-inside">
              <li class="italic">
                The numbers in each row/column represent the run lengths. Your goal is to place black cells to form consecutive runs that match these numbers.
              </li>
              <li class="italic">
                For example, in the below grid, the second column has "1" on top of "3". This means that there should be a single black cell, then at least one empty cell, then 3 consecutive black cells in that column.
              </li>
            </ul>
          </div>
        </template>
        <template #board>
          <PuzzleNonograms :state="solution" class="mx-auto" />
        </template>
      </FreeplayGameViewInstructionPage>
    </template>

    <template #page3>
      <FreeplayGameViewInstructionPage>
        <template #instruction>
          <div>The numbers only define the length of the black blocks, not the space between them. Looking at the right-most column with hint "3", both placements below are valid since each has 3 consecutive black cells.
          </div>
        </template>
        <template #board>
          <div class="flex flex-row justify-between gap-2 text-center">
            <div class="flex flex-col gap-2">
              <PuzzleNonograms :scale="0.7" :state="page3Left" class="mx-auto" />
            </div>
            <div class="flex flex-col gap-2">
              <PuzzleNonograms :scale="0.7" :state="page3Right" class="mx-auto" />
            </div>
          </div>
        </template>
      </FreeplayGameViewInstructionPage>
    </template>

    <template #page4>
      <FreeplayGameViewInstructionPage>
        <template #instruction>
          <div>Similarly, the bottom-most row with hints "1" and "2" can be satisfied in multiple ways - a single black cell, then at least one empty cell, then 2 consecutive black cells.</div>
        </template>
        <template #board>
          <div class="flex flex-row justify-between gap-2 text-center">
            <div class="flex flex-col gap-2">
              <PuzzleNonograms :scale="0.7" :state="page4Left" class="mx-auto" />
            </div>
            <div class="flex flex-col gap-2">
              <PuzzleNonograms :scale="0.7" :state="page4Right" class="mx-auto" />
            </div>
          </div>
        </template>
      </FreeplayGameViewInstructionPage>
    </template>

    <template #page5>
      <FreeplayGameViewInstructionPage>
        <template #instruction>
          <div>
            The puzzle is solved when each row and column contains the exact runs specified by their hints. While
            there may be multiple ways to satisfy individual rows or columns, the correct solution will uniquely satisfy
            all row and column hints simultaneously.
          </div>
          <Separator />
          <div>
            For instance, the unique solution to this puzzle is shown below, as each row and column hint pattern is
            satisfied.
          </div>
        </template>
        <template #board>
          <PuzzleNonograms :state="solution" class="mx-auto" />
        </template>
      </FreeplayGameViewInstructionPage>

      <div class="flex flex-col gap-2"></div>
    </template>

    <template #controls>
      <div>Left click on a cell to cycle between:</div>
      <ul class="list-decimal gap-2 h-full w-full ml-8">
        <li>Placing a box <i class="md-cell bg-black"></i></li>
        <li>Placing a cross <i class="md-cell md-cell-kakurasu-cross"></i></li>
        <li>Clearing the cell</li>
      </ul>
    </template>
  </FreeplayGameViewInstructionSlider>
</template>
