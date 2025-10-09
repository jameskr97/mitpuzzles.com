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
          <p class="mb-2">
           Kakurasu is a logic puzzle where some cells must be marked black (<span class="inline-block h-3 w-3 bg-black rounded"></span>) to meet specific requirements.
          </p>
          <p class="mb-2">
            Columns are numbered <span class="text-gray-500">1, 2, 3,</span> … at the top; rows are numbered <span class="text-gray-500">1, 2, 3,</span> … on the left. These numbers serve as <span class="text-gray-500">weights</span>.
          </p>
          <p>
            Below is an empty example board:
          </p>
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
              To the right of each <span class="font-bold">row</span> is a <span class="text-blue-500">target sum</span>: when you add the <span class="text-gray-500">weights <span class="italic">(column numbers)</span></span>  of the black cells in that row, the result must equal the target.
            </div>
            <div>
              Beneath each <span class="font-bold">column</span> is a <span class="text-blue-500">target sum</span>: when you add the <span class="text-gray-500">weights <span class="italic">(row numbers)</span></span> of the black cells in that column, the result must equal the target.
            </div>
          </div>
        </template>
        <template #board>
          <PuzzleKakurasu :state="boardEmpty" class="mx-auto" />
        </template>
      </FreeplayGameViewInstructionPage>
    </template>

    <template #page3>
      <FreeplayGameViewInstructionPage>
        <template #instruction>
          <div>
            Your <span class="font-bold">goal</span> is to mark <span class="italic">some</span> cells black, so that all row and column sums are matched.
          </div>

          <div>
            Some targets can be achieved in multiple ways but only one arrangement satisfies <span class="italic">all</span> row and column sums together.
          </div>

          <div>
            For example, row 2 with <span class="font-bold text-blue-500">target 5</span> could be <span class="font-bold text-gray-500">1+4</span> or <span class="font-bold text-gray-500">2+3</span>, as in the example shown below.
          </div>
        </template>
        <template #board>
          <div class="flex flex-row justify-between gap-2 text-center overflow-x-scroll">
            <div class="flex flex-col gap-2">
              <PuzzleKakurasu :scale="0.6" :state="page3Left" class="mx-auto" />
              <div>1 + 4 = 5</div>
            </div>
            <div class="flex flex-col gap-2">
              <PuzzleKakurasu :scale="0.6" :state="page3Right" class="mx-auto" />
              <div>2 + 3 = 5</div>
            </div>
          </div>
        </template>
      </FreeplayGameViewInstructionPage>
    </template>

    <template #page4>
      <FreeplayGameViewInstructionPage>
        <template #instruction>
          <div>
            Similarly, column 1 in the board with
            <span class="font-bold text-blue-500">target 6</span>
            below, would be
            <span class="font-bold text-gray-500">3 + 2 + 1</span>
            or
            <span class="font-bold text-gray-500">4 + 2</span></div>
        </template>
        <template #board>
          <div class="flex flex-row justify-between gap-2 text-center overflow-x-scroll">
            <div class="flex flex-col gap-2">
              <PuzzleKakurasu :scale="0.6" :state="page4Right" class="mx-auto" />
              <div>3 + 2 + 1 = 6</div>
            </div>
            <div class="flex flex-col gap-2">
              <PuzzleKakurasu :scale="0.6" :state="page4Left" class="mx-auto" />
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
            The puzzle is solved when all the row and column sums are satisfied together, as in the example board shown below. 
          </div>
        </template>
        <template #board>
          <PuzzleKakurasu :state="solution" class="mx-auto" />
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
