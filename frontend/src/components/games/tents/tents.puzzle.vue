<script setup lang="ts">
import { ModelTentsPuzzle } from "@/components/games/tents/tents.model";
import GameGrid from "@/components/ui/game/game.grid.vue";

defineProps<{
  scale?: number;
}>();

const model = new ModelTentsPuzzle();
</script>

<template>
  <GameGrid
    :rows="6"
    :cols="6"
    :size="scale"
    class="rounded"
    grid-class="border-r-0 max-w-fit"
    @mouse-up="model.onCellClick($event.row, $event.col)"
  >

    <!-- prettier-ignore -->
    <template v-slot:cell="{ row, col }">
      <div class="w-full h-full border-1" :class="{ 'bg-green-400': model.isCellAdjacentToTent(row, col) }">
        <img v-if="model.isCellTent(row, col)" src="/assets/tents/tent.svg" alt="Tent" class="w-full h-full rounded-sm" />
        <img v-else-if="model.isCellTree(row, col)" src="/assets/tents/tree.svg" alt="Tree" class="w-full h-full rounded-sm" />
      </div>
    </template>

  <template v-slot:top="{ col }">
      <div class="text-center font-bold w-full">
        {{ model.getTopNumber(col) }}
      </div>
    </template>

    <template v-slot:left="{ row, size }">
      <div class="grid font-bold text-end align-middle" >
        {{ model.getLeftNumber(row) }}
      </div>
    </template>
  </GameGrid>
</template>
