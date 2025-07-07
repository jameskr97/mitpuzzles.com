<script setup lang="ts">
import FreeplayGameViewInstructionSlider from "@/features/freeplay/FreeplayGameViewInstructionSlider.vue";
import PuzzleLightup from "@/features/games/lightup/lightup.puzzle.vue";
import { useRoute } from "vue-router";
import { useGameLayout } from "@/composables/useGameLayout.ts";
import { computed } from "vue";
import { ACTIVE_GAMES } from "@/constants.ts";
import type { PuzzleDefinition } from "@/services/game/engines/types.ts";

const route = useRoute();
const layout = useGameLayout();
const game_type = route.meta.game_type as string;
const game_type_capitalized = computed(() => game_type.charAt(0).toUpperCase() + game_type.slice(1));
const game_entry = ACTIVE_GAMES[game_type];

const def: PuzzleDefinition = {
  rows: 7,
  cols: 7,
  initial_state: [
    [6, 6, 6, 6, 6, 6, 6],
    [6, 6, 6, 2, 0, 6, 6],
    [6, 2, 6, 6, 6, 6, 6],
    [6, 6, 5, 6, 6, 6, 5],
    [6, 6, 6, 1, 6, 6, 6],
    [3, 5, 6, 6, 6, 6, 6],
    [6, 6, 6, 6, 6, 6, 6],
  ],
};

const board0: PuzzleState = {
  definition: def,
  board: [
    [6, 6, 6, 6, 6, 6, 6],
    [6, 6, 6, 2, 0, 6, 6],
    [6, 2, 6, 6, 6, 6, 6],
    [6, 6, 5, 6, 6, 6, 5],
    [6, 6, 6, 1, 6, 6, 6],
    [3, 5, 6, 6, 6, 6, 6],
    [6, 6, 6, 6, 6, 6, 6],
  ],
};

// @ts-expect-error ignore any missing fields
const board1: PuzzleState = {
  definition: def,
  board: [
    [6, 6, 6, 6, 6, 6, 6],
    [6, 6, 6, 2, 7, 6, 6],
    [6, 2, 6, 6, 6, 6, 6],
    [6, 6, 5, 6, 6, 6, 5],
    [6, 6, 7, 1, 6, 6, 6],
    [3, 5, 6, 6, 6, 6, 6],
    [6, 6, 6, 6, 6, 6, 6],
  ],
};

// @ts-expect-error ignore any missing fields
const board2: PuzzleState = {
  definition: def,
  board: [
    [6, 6, 6, 6, 6, 6, 6],
    [6, 6, 7, 2, 7, 6, 6],
    [6, 2, 7, 6, 6, 7, 7],
    [5, 6, 7, 7, 5, 6, 7],
    [7, 6, 6, 7, 1, 6, 6],
    [7, 3, 5, 7, 6, 6, 6],
    [6, 6, 7, 7, 6, 6, 6],
  ],
};
</script>

<template>
  <FreeplayGameViewInstructionSlider :num_pages="3">
    <template #page1>
      <div class="flex flex-col gap-2 m-2 h-full text-center">
        <div class="text-xl mb-2">
          Light Up is a logic puzzle played on a grid with black and white cells. The goal is to place light bulbs to
          illuminate the entire grid.
        </div>
        <PuzzleLightup :scale="1" :state="board0" class="mx-auto" />
      </div>
    </template>

    <template #page2>
      <div class="flex flex-col gap-2 m-2 h-full text-center">
        <div class="text-xl mb-2">
          Place light bulbs on white cells. Light travels horizontally and vertically, illuminating all cells in its
          path until it hits a black cell. Black cells with numbers indicate exactly how many light bulbs must be placed
          adjacent to them.
        </div>
        <PuzzleLightup :scale="1" :state="board1" class="mx-auto" />
      </div>
    </template>

    <template #page3>
      <div class="flex flex-col gap-2 m-2 h-full text-center">
        <div class="text-xl mb-2">
          The puzzle is solved when all white cells are illuminated, no light bulbs shine on other light bulbs, and all
          numbered black cells have the correct number of adjacent light bulbs. Submit your answer when complete.
        </div>
        <PuzzleLightup :scale="1" :state="board2" class="mx-auto" />
      </div>
    </template>
  </FreeplayGameViewInstructionSlider>
</template>

<style scoped></style>
