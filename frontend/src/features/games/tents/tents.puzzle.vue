<script setup lang="ts">
import { ModelTentsPuzzle } from "@/features/games/tents/tents.model";
import GameGrid from "@/components/game/game.grid.vue";
import { reactive, type Ref } from "vue";

const props = defineProps<{
  scale?: number;
  state: Ref<any>;
}>();

const emits = defineEmits<{
  (e: "game-event", event_type: string, payload: object): void;
}>();

const model = new ModelTentsPuzzle(props.state.value, (event: string, payload: object) => {
  emits("game-event", event, payload);
});
</script>

<template>
  <GameGrid
    :rows="model.ROWS"
    :cols="model.COLS"
    :scale="scale"
    class="rounded"
    @mouse-up="model.onCellClick($event.row, $event.col, $event.input_event)"
    @cell-enter="model.onCellMouseEnter($event.row, $event.col)"
    @cell-leave="model.onCellMouseLeave($event.row, $event.col)"
    @click-gutter-left="model.onRowNumberClick($event.row)"
    @click-gutter-top="model.onColNumberClick($event.col)"
  >
    <!-- prettier-ignore -->
    <template v-slot:cell="{ row, col }">
      <div class="w-full h-full">
        <img v-if="model.isCellTent(row, col)" src="/assets/tents/tent.svg" alt="Tent" class="w-full h-full bg-green-300" />
        <img v-else-if="model.isCellTree(row, col)" src="/assets/tents/tree.svg" alt="Tree" class="w-full h-full bg-green-300" />
        <div v-else-if="model.isCellGreen(row, col)"  class="w-full h-full bg-green-300" />
      </div>
    </template>

    <template v-slot:top="{ col }">
      <div class="font-bold flex justify-center items-center h-full w-full">
        {{ model.getTopNumber(col) }}
      </div>
    </template>

    <template v-slot:left="{ row }">
      <div class="grid h-full font-bold text-end items-center justify-center">
        {{ model.getLeftNumber(row) }}
      </div>
    </template>
  </GameGrid>
</template>
