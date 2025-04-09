<script setup lang="ts">
import GameLayout from "@/components/layout/game.layout.vue";
import { useCurrentPuzzle } from "@/composables";
import Lightup from "@/features/games/lightup/lightup.puzzle.vue";

const { state, push_event } = await useCurrentPuzzle();
</script>

<template>
  <GameLayout>
    <template #instructions>
      <li>The black cells on each row sum up to the number on the right.</li>
      <li>The black cells on each column sum up to the number on the bottom.</li>
      <li>If a black cell is first on its row/column its value is 1. If it is second its value is 2 etc.</li>
      <li>Click a cell to make it black, right click to place an X.</li>
    </template>

    <template v-slot:default="props">
      <Lightup :scale="props.scale" :state="state" />
    </template>
  </GameLayout>
</template>
