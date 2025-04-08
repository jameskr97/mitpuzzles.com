<script setup lang="ts">
import Sudoku from "@/features/games/sudoku/sudoku.puzzle.vue";
import GameLayout from "@/components/layout/game.layout.vue";
import { useCurrentPuzzle } from "@/composables";
const { state, push_event } = await useCurrentPuzzle();

function on_game_event(event_type: string, payload: object) {
  push_event(event_type, payload);
}
</script>

<template>
  <div>
    <p class="text-center text-2xl">Sudoku</p>
    <div class="divider m-0"></div>
    <GameLayout>
      <template #instructions>
        <ul class="list-inside list-decimal">
          <li>The puzzle consists of a 9x9 grid, divided into nine 3x3 subgrids (also called boxes or regions).</li>
          <li>Each row must contain the numbers 1 through 9, with no repeats.</li>
          <li>Each column must contain the numbers 1 through 9, with no repeats.</li>
          <li>Each 3x3 subgrid must also contain the numbers 1 through 9, with no repeats.</li>
          <li>Some numbers are given at the start as clues—these cannot be changed.</li>
          <li>The goal is to fill in all the blank squares following the above rules.</li>
        </ul>
      </template>

      <template v-slot:default="props">
        <Sudoku :scale="props.scale" :state="state" @game-event="on_game_event" />
      </template>
    </GameLayout>
  </div>
</template>

<style>
:root {
  --font-size: 1.5rem;
  --border-thickness: 1px;
  --border-thickness-bold: 3px;
}
</style>
