<script setup lang="ts">
import { getPersistentHighlightSudokuBoard } from "@/features/games/sudoku/getPersistentHighlightSudokuBoard.ts";
import type { PuzzleDefinition, PuzzleState } from "@/services/game/engines/types.ts";
import { InstructionSlider, InstructionPage } from "@/features/freeplay/components";
import PuzzleSudoku from "@/features/games/sudoku/sudoku.puzzle.vue";

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

const RowHighlighted = getPersistentHighlightSudokuBoard({ row: 2 });
const ColHighlighted = getPersistentHighlightSudokuBoard({ col: 6 });
const BoxHighlighted = getPersistentHighlightSudokuBoard({ box: 1 });
</script>

<template>
  <InstructionSlider>
    <template #page1>
      <InstructionPage>
        <template #instruction>
          <div v-html="$t('puzzle:sudoku:intro')"></div>
          <div v-html="$t('puzzle:sudoku:goal')"></div>
        </template>
        <template #board>
          <PuzzleSudoku :state="gameState0" :scale="BOARD_SCALE" />
        </template>
      </InstructionPage>
    </template>

    <template #page2>
      <InstructionPage>
        <template #instruction>
          <div v-html="$t('puzzle:sudoku:rule_row')"></div>
          <div class="italic" v-html="$t('puzzle:sudoku:rule_row_example')"></div>
        </template>
        <template #board>
          <RowHighlighted :state="gameState0" :scale="BOARD_SCALE" />
        </template>
      </InstructionPage>
    </template>

    <template #page3>
      <InstructionPage>
        <template #instruction>
          <div v-html="$t('puzzle:sudoku:rule_col')"></div>
          <div class="italic" v-html="$t('puzzle:sudoku:rule_col_example')"></div>
        </template>
        <template #board>
          <ColHighlighted :state="gameState0" :scale="BOARD_SCALE" />
        </template>
      </InstructionPage>
    </template>

    <template #page4>
      <InstructionPage>
        <template #instruction>
          <div v-html="$t('puzzle:sudoku:rule_box')"></div>
          <div class="italic" v-html="$t('puzzle:sudoku:rule_box_example')"></div>
        </template>
        <template #board>
          <BoxHighlighted :state="gameState0" :scale="BOARD_SCALE" />
        </template>
      </InstructionPage>
    </template>

    <template #controls>
      <ul class="list-disc ml-4">
        <li v-html="$t('puzzle:sudoku:control_select')"></li>
        <li v-html="$t('puzzle:sudoku:control_input')"></li>
      </ul>
    </template>
  </InstructionSlider>
</template>
