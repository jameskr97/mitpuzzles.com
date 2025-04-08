<script setup lang="ts">
import GameLayout from "@/components/layout/game.layout.vue";
import Kakurasu from "@/features/games/kakurasu/kakurasu.puzzle.vue";
</script>

<template>
  <GameLayout>
    <template #left>
      <div class="flex flex-col md:w-full">
        <p class="text-2xl text-center md:text-left">Game Instructions</p>
        <p>The goal is to make some of the cells black in such a way that:</p>
        <ul class="list-inside list-decimal">
          <li>
            The black cells on each row sum up to the number on the right.
          </li>
          <li>
            The black cells on each column sum up to the number on the bottom.
          </li>
          <li>
            If a black cell is first on its row/column its value is 1. If it is
            second its value is 2 etc.
          </li>
          <li>Click a cell to make it black, right click to place an X.</li>
        </ul>
        <div class="divider m-0"></div>
      </div>
    </template>

    <template v-slot:default="props">
      <Kakurasu :scale="props.scale" />
    </template>
  </GameLayout>
</template>
