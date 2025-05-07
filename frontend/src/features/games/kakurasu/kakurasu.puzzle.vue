<script setup lang="ts">
import BoardContainer from "@/features/games/components/board.container.vue";
import BoardBorders from "@/features/games/components/board.borders.vue";
import BoardCells from "@/features/games/components/board.cellgrid.vue";
import BoardInteraction from "@/features/games/components/board.interaction.vue";
import type { Ref } from "vue";
import { createStateMachinePuzzleModel } from "@/features/games/composables/PuzzleModelBase";
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

const borderConfig = {
  outer: { thickness: 1, borderClass: "bg-black" },
};
</script>
<template>
  <BoardContainer
    :rows="m.rows.value"
    :cols="m.cols.value"
    :scale="scale"
    :gutter-top="1"
    :gutter-left="1"
    :gutter-right="1"
    :gutter-bottom="1"
    class-game-cell="border-black"
    :model="m"
    :border-config="borderConfig"
  >
    <BoardBorders />
    <BoardInteraction />
    <BoardCells>
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
    </BoardCells>
  </BoardContainer>
</template>
