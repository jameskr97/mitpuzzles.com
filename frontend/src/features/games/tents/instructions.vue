<script setup lang="ts">
import GameViewInstructionsSlider from "@/components/gameview.instructions.slider.vue";
import PuzzleTents from "@/features/games/tents/tents.puzzle.vue";
import { useRoute } from "vue-router";
import { useGameLayout } from "@/composables/useGameLayout.ts";
import { computed } from "vue";
import { ACTIVE_GAMES } from "@/constants.ts";
import type { PuzzleStateTents } from "@/services/states.ts";

const route = useRoute();
const layout = useGameLayout();
const game_type = route.meta.game_type as string;
const game_type_capitalized = computed(() => game_type.charAt(0).toUpperCase() + game_type.slice(1));
const game_entry = ACTIVE_GAMES[game_type];

// @ts-expect-error ignore any missing fields
const board0: PuzzleStateTents = {
  rows: 6,
  cols: 6,
  row_counts: [2, 1, 1, 1, 1, 1],
  col_counts: [2, 0, 1, 1, 1, 2],
  board: [0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0],
};

// @ts-expect-error ignore any missing fields
const board1: PuzzleStateTents = {
  rows: 6,
  cols: 6,
  row_counts: [2, 1, 1, 1, 1, 1],
  col_counts: [2, 0, 1, 1, 1, 2],
  board: [2, 1, 0, 0, 0, 0, 0, 0, 0, 2, 0, 1, 0, 0, 0, 1, 2, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0],
};

// @ts-expect-error ignore any missing fields
const board2: PuzzleStateTents = {
  rows: 6,
  cols: 6,
  row_counts: [2, 1, 1, 1, 1, 1],
  col_counts: [2, 0, 1, 1, 1, 2],
  board: [2, 1, 0, 0, 2, 0, 2, 0, 0, 2, 0, 1, 0, 0, 0, 1, 2, 0, 0, 2, 0, 1, 0, 1, 2, 0, 0, 1, 0, 0, 0, 1, 0, 2, 0, 0],
};
</script>

<template>
  <GameViewInstructionsSlider :num_pages="3">
    <template #page1>
      <div class="flex flex-col gap-2 m-2 h-full text-center">
        <div class="text-xl mb-2">
          Tents is a logic puzzle where you need to place tents on a grid that contains trees. Numbers on each row and
          column show how many tents must be placed in that line.
        </div>
        <PuzzleTents :scale="2" :state="board0" class="mx-auto" />
      </div>
    </template>

    <template #page2>
      <div class="flex flex-col gap-2 m-2 h-full text-center">
        <div class="text-xl mb-2">
          Each tent must be placed adjacent (horizontally or vertically) to a tree. Tents cannot touch each other, not
          even diagonally. Every tree must have exactly one tent connected to it.
        </div>
        <PuzzleTents :scale="2" :state="board1" class="mx-auto" />
      </div>
    </template>

    <template #page3>
      <div class="flex flex-col gap-2 m-2 h-full text-center">
        <div class="text-xl mb-2">
          The puzzle is solved when all tents are placed according to the rules, with the correct number in each row and
          column. Submit your answer when complete.
        </div>
        <PuzzleTents :scale="2" :state="board2" class="mx-auto" />
      </div>
    </template>
  </GameViewInstructionsSlider>
</template>
