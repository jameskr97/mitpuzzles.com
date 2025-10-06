<script setup lang="ts">
import FreeplayGameViewInstructionSlider from "@/features/freeplay/FreeplayGameViewInstructionSlider.vue";
import { useRoute } from "vue-router";
import { useGameLayout } from "@/composables/useGameLayout.ts";
import { computed } from "vue";
import { ACTIVE_GAMES } from "@/constants.ts";
import type { PuzzleDefinition, PuzzleState } from "@/services/game/engines/types.ts";
import { LightupCell } from "@/services/game/engines/translator.ts";
import PuzzleLightup from "@/features/games/lightup/lightup.puzzle.vue";
import FreeplayGameViewInstructionPage from "@/features/freeplay/FreeplayGameViewInstructionPage.vue";

const route = useRoute();
const layout = useGameLayout();
const game_type = route.meta.game_type as string;
const game_type_capitalized = computed(() => game_type.charAt(0).toUpperCase() + game_type.slice(1));
const game_entry = ACTIVE_GAMES[game_type];

// @ts-expect-error ignore any missing fields
const definition: PuzzleDefinition = { rows: 5, cols: 5 };

const boardPage1: PuzzleState = {
  definition,
  board: [
    [LightupCell.WALL_0, LightupCell.EMPTY, LightupCell.WALL_1, LightupCell.WALL_NO_CONSTRAINT, LightupCell.EMPTY],
    [LightupCell.EMPTY, LightupCell.EMPTY, LightupCell.EMPTY, LightupCell.WALL_2, LightupCell.EMPTY],
    [LightupCell.EMPTY, LightupCell.EMPTY, LightupCell.WALL_2, LightupCell.EMPTY, LightupCell.EMPTY],
    [LightupCell.EMPTY, LightupCell.EMPTY, LightupCell.EMPTY, LightupCell.WALL_3, LightupCell.EMPTY],
    [LightupCell.EMPTY, LightupCell.WALL_2, LightupCell.EMPTY, LightupCell.EMPTY, LightupCell.EMPTY],
  ],
};

const boardPage2 = JSON.parse(JSON.stringify(boardPage1)); // Clone the boardPage1 for page2
boardPage2.board[2][0] = LightupCell.BULB;

const boardPage3 = JSON.parse(JSON.stringify(boardPage1)); // Clone the boardPage1 for page2
boardPage3.board[1][2] = LightupCell.BULB;
boardPage3.board[2][3] = LightupCell.BULB;

const boardPage4 = JSON.parse(JSON.stringify(boardPage1)); // Clone the boardPage1 for page2
boardPage4.board[2][0] = LightupCell.BULB;
boardPage4.board[4][0] = LightupCell.BULB;
boardPage4.board[1][2] = LightupCell.BULB;
boardPage4.board[3][2] = LightupCell.BULB;

const boardPage5 = JSON.parse(JSON.stringify(boardPage1)); // Clone the boardPage1 for page2
boardPage5.board[1][2] = LightupCell.BULB;
boardPage5.board[2][3] = LightupCell.BULB;
boardPage5.board[3][1] = LightupCell.BULB;
boardPage5.board[3][4] = LightupCell.BULB;
boardPage5.board[4][0] = LightupCell.BULB;
boardPage5.board[4][3] = LightupCell.BULB;
</script>

<template>
  <FreeplayGameViewInstructionSlider :num_pages="5">
    <template #page1>
      <FreeplayGameViewInstructionPage>
        <template #instruction>
          <div class="mb-2">
            Light Up is a logic puzzle played on a grid of black and white cells. An example board is shown below. Your
            goal is to place light bulbs on white cells so that
            <span class="font-bold">all white cells are illuminated.</span>
          </div>
        </template>
        <template #board>
          <PuzzleLightup :state="boardPage1" :scale="1" class="mx-auto" />
        </template>
      </FreeplayGameViewInstructionPage>
    </template>

    <template #page2>
      <FreeplayGameViewInstructionPage>
        <template #instruction>
          <div>
            When placed on a square,
            <span class="font-bold">a light bulb illuminates all cells in its row and column</span> until the light is
            blocked by a black cell.
          </div>
        </template>
        <template #board>
          <PuzzleLightup :state="boardPage2" :scale="1" class="mx-auto" />
        </template>
      </FreeplayGameViewInstructionPage>
    </template>

    <template #page3>
      <FreeplayGameViewInstructionPage>
        <template #instruction>
          <div>
            Some black cells contain numbers. These indicate exactly
            <span class="font-bold">how many bulbs must be placed next to it</span>
            (horizontally or vertically adjacent). Cells marked "0" must not have any bulbs next to them. Unnumbered black cells can have any
            number of adjacent bulbs.
          </div>
          <div>In the example below, the two bulbs placed satisfy the numbers "2", "2" and "1" next to them:</div>
        </template>
        <template #board>
          <PuzzleLightup :state="boardPage3" :scale="1" class="mx-auto" />
        </template>
      </FreeplayGameViewInstructionPage>
    </template>

    <template #page4>
      <FreeplayGameViewInstructionPage>
        <template #instruction>
          <div>
            No two bulbs may be placed such that <span class="font-bold">one illuminates the other</span>. Two bulbs may
            share a row or column as long as there is a black square between them.
          </div>
          <div>
            The example below shows an <span class="font-bold">invalid</span> placement (red) and a
            <span class="font-bold">valid</span> placement (green) of two bulbs sharing a column.
          </div>
        </template>
        <template #board>
          <PuzzleLightup :state="boardPage4" :scale="1" class="mx-auto" />
        </template>
      </FreeplayGameViewInstructionPage>
    </template>

    <template #page5>
      <FreeplayGameViewInstructionPage>
        <template #instruction>
          <div>
            The puzzle is solved when
            <span class="font-bold">all white cells are lit, no two bulbs illuminate each other,</span> and all numbered
            black cells have <span class="font-bold">the correct number of adjacent bulbs</span>.
          </div>
        </template>
        <template #board>
          <PuzzleLightup :state="boardPage5" :scale="1" class="mx-auto" />
        </template>
      </FreeplayGameViewInstructionPage>
    </template>

    <template #controls>
      <div>Left click to cycle forward, right click to cycle backward between:</div>
      <ul class="list-decimal gap-2 h-full max-w-fit ml-8">
        <li>Placing a lightbulb <i class="md-cell md-cell-lightup-bulb bg-yellow-200 border rounded"></i></li>
        <li>
          Marking the cell with an <i class="md-cell md-cell-lightup-cross rounded"></i> (to indicate no lightbulb will
          go there)
        </li>
        <li>Clearing the cell.</li>
      </ul>
    </template>
  </FreeplayGameViewInstructionSlider>
</template>

<style scoped></style>
