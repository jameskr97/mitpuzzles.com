<script setup lang="ts">
import FreeplayGameViewInstructionSlider from "@/features/freeplay/FreeplayGameViewInstructionSlider.vue";
import { useRoute } from "vue-router";
import { getPersistentHighlightSudokuBoard } from "@/features/games/sudoku/getPersistentHighlightSudokuBoard.ts";
import type { PuzzleDefinition, PuzzleState } from "@/services/game/engines/types.ts";
import { useDemoSudokuController } from "@/features/games/sudoku/useDemoSudokuController.ts";
import PuzzleSudoku from "@/features/games/sudoku/sudoku.puzzle.vue";
import FreeplayGameViewInstructionPage from "@/features/freeplay/FreeplayGameViewInstructionPage.vue";

const route = useRoute();
const BOARD_SCALE = 0.7;
const def: Partial<PuzzleDefinition> = {
  rows: 9,
  cols: 9,
  initial_state: [
    [1, 5, 6, 0, 8, 0, 0, 2, 0],
    [0, 0, 0, 1, 2, 0, 6, 5, 0],
    [3, 4, 2, 6, 0, 5, 0, 0, 1],
    [0, 8, 5, 0, 0, 3, 0, 4, 0],
    [4, 0, 0, 2, 0, 0, 8, 7, 5],
    [0, 7, 9, 4, 0, 8, 3, 1, 0],
    [0, 0, 0, 0, 3, 1, 4, 0, 2],
    [9, 2, 4, 5, 0, 6, 1, 3, 8],
    [8, 3, 1, 0, 4, 0, 0, 0, 7],
  ],
};

// prettier-ignore
const gameState0: PuzzleState = {
  // @ts-expect-error partial definition
  definition: def,
  board: [
    [1, 5, 6, 0, 8, 0, 0, 2, 0],
    [0, 0, 0, 1, 2, 0, 6, 5, 0],
    [3, 4, 2, 6, 0, 5, 0, 0, 1],
    [0, 8, 5, 0, 0, 3, 0, 4, 0],
    [4, 0, 0, 2, 0, 0, 8, 7, 5],
    [0, 7, 9, 4, 0, 8, 3, 1, 0],
    [0, 0, 0, 0, 3, 1, 4, 0, 2],
    [9, 2, 4, 5, 0, 6, 1, 3, 8],
    [8, 3, 1, 0, 4, 0, 0, 0, 7]
  ]
};

const gameState0Solution: PuzzleState = {
  // @ts-expect-error partial definition
  definition: def,
  board: [
    [1, 5, 6, 3, 8, 7, 9, 2, 4],
    [7, 9, 8, 1, 2, 4, 6, 5, 3],
    [3, 4, 2, 6, 9, 5, 7, 8, 1],
    [6, 8, 5, 7, 1, 3, 2, 4, 9],
    [4, 1, 3, 2, 6, 9, 8, 7, 5],
    [2, 7, 9, 4, 5, 8, 3, 1, 6],
    [5, 6, 7, 8, 3, 1, 4, 9, 2],
    [9, 2, 4, 5, 7, 6, 1, 3, 8],
    [8, 3, 1, 9, 4, 2, 5, 6, 7],
  ],
};

const { puzzle_state: demo_puzzle_state, interact: demo_interact } = useDemoSudokuController(def, {
  cycle_mode: false,
  allow_prefilled_modification: false,
});

const RowHighlighted = getPersistentHighlightSudokuBoard({ row: 2 });
const ColHighlighted = getPersistentHighlightSudokuBoard({ col: 6 });
const BoxHighlighted = getPersistentHighlightSudokuBoard({ box: 1 });
</script>

<template>
  <FreeplayGameViewInstructionSlider :num_pages="4">
    <template #page1>
      <FreeplayGameViewInstructionPage>
        <template #instruction>
          <div class="text-black">
            <div class="flex flex-col gap-2">
              <div>
                Sudoku is a logic puzzle played on a square grid. The grid is divided into several
                <span class="font-bold">smaller square sub-grids</span>. For example, below is a 9x9 sudoku
                board, divided into 9 3x3 boxes.
              </div>
              <div>
                In order to solve a sudoku board, every square must be
                <span class="font-bold">filled in with a number</span> from 1 to 9. Your job is figuring out which
                numbers go into the empty squares by looking at numbers that are already filled in.
              </div>
            </div>
          </div>
        </template>
        <template #board>
          <PuzzleSudoku :state="gameState0" :scale="BOARD_SCALE" class="mx-auto"></PuzzleSudoku>
        </template>
      </FreeplayGameViewInstructionPage>
    </template>

    <template #page2>
      <FreeplayGameViewInstructionPage>
        <template #instruction>
          <div>
            First, each <strong>row</strong> must include every number from 1 to 9, and each number must appear exactly
            <strong>once</strong>.
          </div>
          <div class="italic">
            The highlighted row has the numbers 3, 4, 2, 6, 5, and 1. It needs the numbers 7, 8, and 9 for the row to be
            complete.
          </div>
        </template>
        <template #board>
          <RowHighlighted :state="gameState0" :scale="BOARD_SCALE" class="mx-auto"></RowHighlighted>
        </template>
      </FreeplayGameViewInstructionPage>
    </template>

    <template #page3>
      <FreeplayGameViewInstructionPage>
        <template #instruction>
          <div>
            Second, each <strong>column</strong> must include every number from 1 to 9, and each number must appear
            exactly <strong>once</strong>.
          </div>
          <div class="italic">
            The highlighted column has the numbers 6, 8, 3, 4, and 1. It needs the numbers 2, 5, 7, and 9 for the column
            to be complete.
          </div>
        </template>
        <template #board>
          <ColHighlighted :state="gameState0" :scale="BOARD_SCALE" class="mx-auto"></ColHighlighted>
        </template>
      </FreeplayGameViewInstructionPage>
    </template>

    <template #page4>
      <FreeplayGameViewInstructionPage>
        <template #instruction>
          <div>
            Third, each <strong>3x3 sub-grid</strong> must include every number from 1 to 9, and each number must appear exactly
            <strong>once</strong>.
          </div>
          <div class="italic">
            The highlighted box has the numbers 8, 1, 2, 6, and 5. It needs the numbers 3, 4, 7 and 9 for the box to be
            complete.
          </div>
        </template>
        <template #board>
          <BoxHighlighted :state="gameState0" :scale="BOARD_SCALE" class="mx-auto"></BoxHighlighted>
        </template>
      </FreeplayGameViewInstructionPage>
    </template>

<!--    <template #page5>-->
<!--      <FreeplayGameViewInstructionPage>-->
<!--        <template #instruction>-->
<!--          <p>-->
<!--             The game is solved when each square is filled with a number from 1 to 9, following these rules.-->
<!--          </p>-->
<!--          <br>-->
<!--          <p>-->
<!--            Below is an example of a solved board.-->
<!--          </p>-->
<!--        </template>-->
<!--        <template #board>-->
<!--          put solved board here-->
<!--&lt;!&ndash;          <BoxHighlighted :state="gameState0" :scale="BOARD_SCALE" class="mx-auto"></BoxHighlighted>&ndash;&gt;-->
<!--        </template>-->
<!--      </FreeplayGameViewInstructionPage>-->
<!--    </template>-->

    <template #controls>
      <ul class="list-disc ml-4">
        <li>Click on a cell to select it.</li>
        <li>
          Enter a number in the selected cell (dark blue) by pressing number keys 1 to 9 on your keyboard. Numbers you
          entered will appear in <span class="text-sky-600 font-bold">blue</span>, and can be changed again later.
        </li>
      </ul>
    </template>
  </FreeplayGameViewInstructionSlider>
</template>
