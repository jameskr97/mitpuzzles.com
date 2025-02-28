<script setup lang="ts">
import Tents from "@/components/games/tents/tents.puzzle.vue";
import GameLayout from "@/components/ui/layout/game.layout.vue";
</script>

<template>
  <GameLayout>
    <template #left>
      <div class="flex flex-col md:w-full">
        <p class="text-2xl text-center md:text-left">Game Instructions</p>
        <ul class="list-inside list-decimal">
          <li>
            Pair each tree with a tent adjacent horizontally or vertically. This
            should be a 1 to 1 relation.
          </li>
          <li>Tents never touch each other even diagonally</li>
          <li>
            The clues outside the grid indicate the number of tents on that
            row/column.
          </li>
        </ul>
        <div class="divider m-0"></div>
      </div>
    </template>
    <template v-slot:default="props">
      <Tents :scale="props.scale" class="border-5"/>
    </template>
  </GameLayout>
</template>
