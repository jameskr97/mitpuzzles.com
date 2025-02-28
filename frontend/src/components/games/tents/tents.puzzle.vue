<script setup lang="ts">
import { ModelTentsPuzzle } from "@/components/games/tents/tents.model";
import GameGrid from "@/components/ui/game/game.grid.vue";

defineProps({
  scale: { type: Number, required: false, default: 1 },
});

const model = new ModelTentsPuzzle();
</script>

<template>
  <GameGrid
    :rows="6"
    :cols="6"
    :size="scale"
    class="rounded"
    grid-class="border-r-0"
    @mouse-up="model.onCellClick($event.row, $event.col)"
  >
    <template v-slot:cell="{ row, col }">
      <div
        class="w-full h-full border-1"
        :class="{
          'bg-green-400': model.isCellAdjacentToTent(row, col),
        }"
      >
        <div
          v-if="model.isCellTent(row, col)"
          class="w-full h-full rounded-sm bg-[url(/assets/tents/tent.svg)] bg-contain"
        ></div>
        <div
          v-if="model.isCellTree(row, col)"
          class="w-full h-full rounded-sm bg-[url(/assets/tents/tree.svg)] bg-contain"
        ></div>
      </div>
    </template>

    <template v-slot:top="{ col, size }">
      <div class="text-center font-bold" :style="{ fontSize: size + 'rem' }">
        {{ model.getTopNumber(col) }}
      </div>
    </template>

    <template v-slot:left="{ row, size }">
      <div class="text-center font-bold" :style="{ fontSize: size + 'rem' }">
        {{ model.getLeftNumber(row) }}
      </div>
    </template>
  </GameGrid>
</template>
