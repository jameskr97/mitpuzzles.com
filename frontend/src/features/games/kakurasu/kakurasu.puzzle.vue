<script setup lang="ts">
import GameGrid from "@/components/game/game.grid.vue";
import type { Ref } from "vue";
import { createStateMachinePuzzleModel } from "@/features/games/composables/puzzleModelBase.ts";
import type { PuzzleStateKakurasu } from "@/services/states.ts";

const props = defineProps<{
  scale?: number;
  state: Ref<PuzzleStateKakurasu>;
}>();

const emits = defineEmits<{
  (e: "game-event", event_type: string, payload: object): void;
}>();

enum KakurasuCellStates {
  Empty = 0,
  Filled = 1,
  Crossed = 2,
  NUM_STATES,
}
const m = createStateMachinePuzzleModel<PuzzleStateKakurasu>(props.state, KakurasuCellStates.NUM_STATES, (e, p) =>
  emits("game-event", e, p),
);
</script>
<template>
  <GameGrid
    :rows="m.rows.value"
    :cols="m.cols.value"
    :scale="scale"
    :cell-size="12"
    class-game-cell="border-black"
    :model="m"
  >
    <template v-slot:cell="{ row, col }">
      <div
        v-if="m.getCellState(row, col) === KakurasuCellStates.Filled"
        class="border-1 bg-black border-white h-full w-full"
      ></div>
      <div
        v-if="m.getCellState(row, col) === KakurasuCellStates.Crossed"
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
        {{ m.state.value.row_sum[props.row] }}
      </div>
    </template>

    <template v-slot:bottom="props">
      <div class="grid place-items-center text-blue-500">
        {{ m.state.value.col_sum[props.col] }}
      </div>
    </template>
  </GameGrid>
</template>
