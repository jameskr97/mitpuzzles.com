<script setup lang="ts">
import Tents from "@/components/games/tents/tents.puzzle.vue";
import GameLayout from "@/components/ui/layout/game.layout.vue";
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
        <li>Pair each tree with a tent adjacent horizontally or vertically. This should be a 1 to 1 relation.</li>
        <li>Tents never touch each other even diagonally</li>
        <li>The clues outside the grid indicate the number of tents on that row/column.</li>
      </template>
      <template v-slot:default="props">
        <Tents :scale="props.scale" :state="state" @game-event="on_game_event" />
      </template>
    </GameLayout>
  </div>
</template>
