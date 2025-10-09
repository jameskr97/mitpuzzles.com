<script setup lang="ts">
import FreeplayGameViewInstructionSlider from "@/features/freeplay/FreeplayGameViewInstructionSlider.vue";
import PuzzleMosaic from "@/features/games/mosaic/mosaic.puzzle.vue";
import type { PuzzleDefinition, PuzzleState } from "@/services/game/engines/types.ts";
import { MosaicCell } from "@/services/game/engines/translator.ts";
import FreeplayGameViewInstructionPage from "@/features/freeplay/FreeplayGameViewInstructionPage.vue";

// @ts-expect-error ignore any missing fields
const definition: PuzzleDefinition = {
  rows: 4,
  cols: 4,
  initial_state: [
    [-1, 0, 0, -1],
    [-1, 1, 0, -1],
    [3, -1, 2, 1],
    [3, 4, -1, 1],
  ],
};

const boardPage1: PuzzleState = {
  definition,
  board: [
    [MosaicCell.UNMARKED, MosaicCell.UNMARKED, MosaicCell.UNMARKED, MosaicCell.UNMARKED],
    [MosaicCell.UNMARKED, MosaicCell.UNMARKED, MosaicCell.UNMARKED, MosaicCell.UNMARKED],
    [MosaicCell.UNMARKED, MosaicCell.UNMARKED, MosaicCell.UNMARKED, MosaicCell.UNMARKED],
    [MosaicCell.UNMARKED, MosaicCell.UNMARKED, MosaicCell.UNMARKED, MosaicCell.UNMARKED],
  ],
  solved: false,
  immutable_cells: [],
  violations: [],
};

const boardPage2: PuzzleState = {
  definition,
  board: [
    [MosaicCell.UNMARKED, MosaicCell.UNMARKED, MosaicCell.UNMARKED, MosaicCell.UNMARKED],
    [MosaicCell.UNMARKED, MosaicCell.UNMARKED, MosaicCell.UNMARKED, MosaicCell.UNMARKED],
    [MosaicCell.UNMARKED, MosaicCell.UNMARKED, MosaicCell.UNMARKED, MosaicCell.UNMARKED],
    [MosaicCell.UNMARKED, MosaicCell.UNMARKED, MosaicCell.UNMARKED, MosaicCell.UNMARKED],
  ],
  solved: false,
  immutable_cells: [],
  violations: [],
};

const boardPage3: PuzzleState = {
  definition,
  board: [
    [MosaicCell.UNMARKED, MosaicCell.UNMARKED, MosaicCell.UNMARKED, MosaicCell.UNMARKED],
    [MosaicCell.CROSS, MosaicCell.CROSS, MosaicCell.UNMARKED, MosaicCell.UNMARKED],
    [MosaicCell.SHADED, MosaicCell.CROSS, MosaicCell.UNMARKED, MosaicCell.UNMARKED],
    [MosaicCell.SHADED, MosaicCell.SHADED, MosaicCell.UNMARKED, MosaicCell.UNMARKED],
  ],
  solved: false,
  immutable_cells: [],
  violations: [],
};

const boardPage4: PuzzleState = {
  definition,
  board: [
    [MosaicCell.CROSS, MosaicCell.CROSS, MosaicCell.CROSS, MosaicCell.CROSS],
    [MosaicCell.CROSS, MosaicCell.CROSS, MosaicCell.CROSS, MosaicCell.CROSS],
    [MosaicCell.SHADED, MosaicCell.CROSS, MosaicCell.CROSS, MosaicCell.CROSS],
    [MosaicCell.SHADED, MosaicCell.SHADED, MosaicCell.SHADED, MosaicCell.CROSS],
  ],
  solved: false,
  immutable_cells: [],
  violations: [],
};
</script>

<template>
  <FreeplayGameViewInstructionSlider :num_pages="4" slide-class="min-h-100">
    <template #page1>
      <FreeplayGameViewInstructionPage>
        <template #instruction>
          <div>
            <p class="mb-4">
              Mosaic is a logic puzzle in which your goal is to determine which cells should be shaded by marking them <span class="font-black">black</span> (<span class="inline-block h-3 w-3 bg-black"></span>), using the numbers shown on some cells as clues.
            </p>
            <p>
              An example board is shown below.
            </p>
          </div>
        </template>
        <template #board>
          <PuzzleMosaic :state="boardPage1" :scale="1.5" class="mx-auto" />
        </template>
      </FreeplayGameViewInstructionPage>
    </template>

    <template #page2>
      <FreeplayGameViewInstructionPage>
        <template #instruction>
          <div>
            <p class="mb-4">
              The numbers show how many of the adjacent cells should be shaded (horizontally, vertically and diagonally), <span class="font-bold italic">including the numbered cell itself</span>.
            </p>
            <p>For instance, the "2" in the example board means 2 of the 9 surrounding cells (including the 2 itself) should be shaded.</p>
          </div>
        </template>
        <template #board>
          <PuzzleMosaic :state="boardPage2" :scale="1.5" class="mx-auto" />
        </template>
      </FreeplayGameViewInstructionPage>
    </template>

    <template #page3>
      <FreeplayGameViewInstructionPage>
        <template #instruction>
          <div>
            <p class="mb-4">
              Mark cells black which you believe should be shaded. You can also mark cells white to indicate that they should not be shaded.
            </p>
            <p>
              In the example below, several cells have been marked black and white, satisfying both 3s in the first column.
            </p>
          </div>
        </template>
        <template #board>
          <PuzzleMosaic :state="boardPage3" :scale="1.5" class="mx-auto" />
        </template>
      </FreeplayGameViewInstructionPage>
    </template>

    <template #page4>
      <FreeplayGameViewInstructionPage>
        <template #instruction>
          <div>
            <p class="mb-4">
              A puzzle is solved when all cells that should be shaded are marked black and the remaining cells are unmarked or marked white.
            </p>
            <p>
              Below is an example of a solved board.
            </p>
          </div>
        </template>
        <template #board>
          <PuzzleMosaic :state="boardPage4" :scale="1.5" class="mx-auto" />
        </template>
      </FreeplayGameViewInstructionPage>
    </template>

    <template #controls>
      <div>Left click to cycle forward, right click to cycle backward between:</div>
      <ul class="list-decimal gap-2 h-full w-full ml-8">
        <li>Marking a cell black <span class="inline-block h-3 w-3 bg-black"></span> (shaded)</li>
        <li>Marking a cell white <span class="inline-block h-3 w-3 bg-white border border-gray-400"></span> (not shaded)</li>
        <li>Clearing the cell</li>
      </ul>
    </template>
  </FreeplayGameViewInstructionSlider>
</template>
