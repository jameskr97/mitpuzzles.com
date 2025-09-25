<script setup lang="ts">
import FreeplayGameViewInstructionSlider from "@/features/freeplay/FreeplayGameViewInstructionSlider.vue";
import PuzzleKakurasu from "@/features/games/kakurasu/kakurasu.puzzle.vue";
import type { KakurasuMeta, PuzzleDefinition, PuzzleState } from "@/services/game/engines/types.ts";
import { Separator } from "@/components/ui/separator";
import FreeplayGameViewInstructionPage from "@/features/freeplay/FreeplayGameViewInstructionPage.vue";

// @ts-expect-error ignore any missing fields
const def: PuzzleDefinition<KakurasuMeta> = {
  rows: 4,
  cols: 4,
  meta: {
    row_sums: [1, 5, 1, 0],
    col_sums: [6, 0, 0, 2],
  },
};

const boardEmpty: PuzzleState<KakurasuMeta> = {
  definition: def,
  board: [
    [0, 0, 0, 0],
    [0, 0, 0, 0],
    [0, 0, 0, 0],
    [0, 0, 0, 0],
  ],
};

const boardHighlight: Partial<PuzzleState<KakurasuMeta>> = {
  definition: def,
  board: [
    [0, 0, 0, 0],
    [1, 1, 1, 1],
    [0, 0, 0, 0],
    [0, 0, 0, 0],
  ],
};

// @ts-expect-error ignore any missing fields
const solution: Partial<PuzzleState<KakurasuMeta>> = {
  definition: def,
  board: [
    [1, 0, 0, 0],
    [1, 0, 0, 1],
    [1, 0, 0, 0],
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

const page3Left: Partial<PuzzleState<KakurasuMeta>> = {
  definition: def,
  board: [
    [0, 0, 0, 0],
    [1, 0, 0, 1],
    [0, 0, 0, 0],
    [0, 0, 0, 0],
  ],
};

const page3Right: Partial<PuzzleState<KakurasuMeta>> = {
  definition: def,
  board: [
    [0, 0, 0, 0],
    [0, 1, 1, 0],
    [0, 0, 0, 0],
    [0, 0, 0, 0],
  ],
};

const page4Right: Partial<PuzzleState<KakurasuMeta>> = {
  definition: def,
  board: [
    [1, 0, 0, 0],
    [1, 0, 0, 0],
    [1, 0, 0, 0],
    [0, 0, 0, 0],
  ],
};

const page4Left: Partial<PuzzleState<KakurasuMeta>> = {
  definition: def,
  board: [
    [0, 0, 0, 0],
    [1, 0, 0, 0],
    [0, 0, 0, 0],
    [1, 0, 0, 0],
  ],
};
</script>

<template>
  <FreeplayGameViewInstructionSlider :num_pages="5" slide-class="min-h-100">
    <template #page1>
      <FreeplayGameViewInstructionPage>
        <template #instruction>
          <div class="mb-2">
            Kakurasu is a logic puzzle played on a grid where you mark some cells black to meet specific requirements.
          </div>
        </template>
        <template #board>
          <PuzzleKakurasu :scale="1" :state="boardEmpty" class="mx-auto" />
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
                The sum of the column numbers of all black cells in a row equals the target sum for that row.
              </li>
              <li class="italic">
                The sum of the row numbers of all black cells in a column equals the target sum for that column.
              </li>
            </ul>
          </div>
        </template>
        <template #board>
          <PuzzleKakurasu :state="solution" class="mx-auto" />
        </template>
      </FreeplayGameViewInstructionPage>
    </template>

    <template #page3>
      <FreeplayGameViewInstructionPage>
        <template #instruction>
          <div>There are usually multiple ways to satisfy individual row and column target-sums.</div>
          <div>The row sum of 5 can be made two ways.</div>
        </template>
        <template #board>
          <div class="flex flex-row justify-between gap-2 text-center">
            <div class="flex flex-col gap-2">
              <PuzzleKakurasu :scale="0.8" :state="page3Left" class="mx-auto" />
              <div>1 + 4 = 5</div>
            </div>
            <div class="flex flex-col gap-2">
              <PuzzleKakurasu :scale="0.8" :state="page3Right" class="mx-auto" />
              <div>2 + 3 = 5</div>
            </div>
          </div>
        </template>
      </FreeplayGameViewInstructionPage>
    </template>

    <template #page4>
      <FreeplayGameViewInstructionPage>
        <template #instruction>
          <div>The column sum of 6 can also be made two ways.</div>
        </template>
        <template #board>
          <div class="flex flex-row justify-between gap-2 text-center">
            <div class="flex flex-col gap-2">
              <PuzzleKakurasu :scale="0.8" :state="page4Right" class="mx-auto" />
              <div>3 + 2 + 1 = 6</div>
            </div>
            <div class="flex flex-col gap-2">
              <PuzzleKakurasu :scale="0.8" :state="page4Left" class="mx-auto" />
              <div>4 + 2 = 6</div>
            </div>
          </div>
        </template>
      </FreeplayGameViewInstructionPage>
    </template>

    <template #page5>
      <FreeplayGameViewInstructionPage>
        <template #instruction>
          <div>
            The puzzle is solved when the black cells in each row/column add up to their corresponding target-sum. While
            there may be multiple ways to satisfy individual rows or columns, the correct solution will uniquely satisfy
            all row and column sums simultaneously.
          </div>
          <Separator />
          <div>
            For instance, the unique solution to this puzzle is shown below, as each row and column target-sum are
            satisfied.
          </div>
        </template>
        <template #board>
          <PuzzleKakurasu :state="solution" class="mx-auto" />
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
