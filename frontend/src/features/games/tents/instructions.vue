<script setup lang="ts">
import FreeplayGameViewInstructionSlider from "@/features/freeplay/FreeplayGameViewInstructionSlider.vue";
import type { PuzzleState, TentsMeta } from "@/services/game/engines/types.ts";
import PuzzleTents from "@/features/games/tents/tents.puzzle.vue";
import FreeplayGameViewInstructionPage from "@/features/freeplay/FreeplayGameViewInstructionPage.vue";
import { TentsCell } from "@/services/game/engines/translator.ts";

const definition = {
  rows: 4,
  cols: 4,
  meta: {
    row_tent_counts: [2, 0, 1, 1],
    col_tent_counts: [1, 1, 1, 1],
  },
};

const boardPage1: PuzzleState<TentsMeta> = {
  // @ts-expect-error intentionally partially defined
  definition,
  board: [
    [0, 0, 0, 0],
    [1, 0, 1, 1],
    [0, 0, 0, 0],
    [0, 0, 1, 0],
  ],
};

const boardPage2 = JSON.parse(JSON.stringify(boardPage1));
boardPage2.board[2][2] = TentsCell.TENT;
boardPage2.board[3][3] = TentsCell.TENT;

const boardPage3 = JSON.parse(JSON.stringify(boardPage1));
boardPage3.board[0][0] = TentsCell.TENT;
boardPage3.board[0][2] = TentsCell.TENT;
boardPage3.board[2][3] = TentsCell.TENT;
boardPage3.board[3][1] = TentsCell.TENT;
</script>

<template>
  <FreeplayGameViewInstructionSlider :num_pages="4">
    <template #page1>
      <FreeplayGameViewInstructionPage>
        <template #instruction>
          <div class="mb-2">
            Tents is a logic puzzle played on a grid with trees <i class="md-cell md-cell-tree"></i> and empty cells.
            Your job is to place tents <i class="md-cell md-cell-tent"></i> next to trees such that all constraints are
            satisfied.
          </div>
          <ul class="list-disc list-inside">
            <li>Tents never touch each other, even diagonally.</li>
            <li>The number of tents in each row and column matches the target numbers on the edges of the grid.</li>
          </ul>
          <div>
            The puzzle is solved when all these conditions are met. The following pages will explain each type of
            constraint.
          </div>
        </template>
        <template #board>
          <PuzzleTents :state="boardPage1" class="mt-auto mx-auto" />
        </template>
      </FreeplayGameViewInstructionPage>
    </template>

    <template #page2>
      <FreeplayGameViewInstructionPage>
        <template #instruction>
          <div>
            Tents must not touch each other, including diagonally. So, once you place a tent, cells horizontally,
            vertically, and diagonally adjacent to it must be tent-free.
          </div>
          <div>
            For instance, the configuration of tents below is <span class="font-bold">invalid</span> because the two
            tents touch each other diagonally:
          </div>
        </template>
        <template #board>
          <PuzzleTents :state="boardPage2" :scale="1" class="mx-auto" />
        </template>
      </FreeplayGameViewInstructionPage>
    </template>

    <template #page3>
      <FreeplayGameViewInstructionPage>
        <template #instruction>
          <div>The numbers on the edges indicate exactly how many tents are in that row or column.</div>
          <ul class="list-disc list-inside">
            <li>
              For instance, the first row has a 2, requiring two tents, while the second row has 0, so it contains no
              tents.
            </li>
            <li>The first column has 1, so there will be exactly one tent in that column.</li>
          </ul>
        </template>
        <template #board>
          <PuzzleTents :state="boardPage3" :scale="1" class="mx-auto" />
        </template>
      </FreeplayGameViewInstructionPage>
    </template>

    <template #page4>
      <FreeplayGameViewInstructionPage>
        <template #instruction>
          <div class="mx-auto">
            Every tree is paired with a unique tent, placed adjacent horizontally or vertically.
          </div>
          <div>
            Multiple tents may be next to a tree,
            <span class="font-bold">but only one of them will be paired with it</span>
            in the final solution, ensuring a global 1–1 tree–tent pairing across the grid.
          </div>
        </template>
        <template #board>
          <PuzzleTents :state="boardPage3" :scale="1" class="mx-auto" />
        </template>
      </FreeplayGameViewInstructionPage>
    </template>

    <template #controls>
      <div>Left click to cycle forward, right click to cycle backward between:</div>
      <ul class="list-disc">
        <li>Placing a tent <i class="md-cell md-cell-tent"></i></li>
        <li>Marking the cell as tent-free <i class="md-cell bg-green-300 rounded"></i></li>
        <li>Clearing the cell</li>
      </ul>
    </template>
  </FreeplayGameViewInstructionSlider>
</template>
