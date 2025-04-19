<script setup lang="ts">
import { KakurasuCellStates, ModelKakurasuPuzzle } from "@/features/games/kakurasu/kakurasu.model";
import GameGrid from "@/components/game/game.grid.vue";
import type { Ref } from "vue";

const props = defineProps<{
  scale?: number;
  state: Ref<any>;
}>();

const emits = defineEmits<{
  (e: "game-event", event_type: string, payload: object): void;
}>();

const model = new ModelKakurasuPuzzle(props.state.value, (event: string, payload: object) => {
  emits("game-event", event, payload);
});
//
</script>
<template>
  <GameGrid
    :rows="model.ROWS"
    :cols="model.COLS"
    :scale="scale"
    :cell-size="12"
    class-game-cell="border-black"
    @cell-click="model.onCellClick($event.row, $event.col, $event.input_event)"
    @cell-right-click="model.onCellClick($event.row, $event.col, $event.input_event)"
  >
    <template v-slot:cell="{ row, col }">
      <div
        v-if="model.getCellState(row, col) === KakurasuCellStates.Filled"
        class="border-1 bg-black border-white h-full w-full"
      ></div>
      <div
        v-if="model.getCellState(row, col) === KakurasuCellStates.Crossed"
        class="bg-[url(/assets/kakurasu/cross.svg)] bg-contain w-full h-full"
      ></div>
    </template>

    <template v-slot:top="props">
      <div class="flex justify-center items-center text-gray-400">
        {{ props.col + 1 }}
      </div>
    </template>

    <template v-slot:left="props">
      <div class="flex justify-center items-center text-gray-400">
        {{ props.row + 1 }}
      </div>
    </template>

    <template v-slot:right="props">
      <div class="grid place-items-center text-blue-500">
        {{ model.store.row_sum[props.row] }}
      </div>
    </template>

    <template v-slot:bottom="props">
      <div class="grid place-items-center text-blue-500">
        {{ model.store.col_sum[props.row] }}
      </div>
    </template>
  </GameGrid>
</template>
