<script setup lang="ts">
import BoardContainer from "@/features/games/components/board.container.vue";
import BoardBorders from "@/features/games/components/board.borders.vue";
import BoardCells from "@/features/games/components/board.cellgrid.vue";
import BoardInteraction from "@/features/games/components/board.interaction.vue";
import type { Ref } from "vue";
import { createStateMachinePuzzleModel } from "@/features/games/composables/PuzzleModelBase";
import type { PuzzleStateKakurasu, PuzzleStateNonograms } from "@/services/states.ts";

const props = defineProps<{
  scale?: number;
  state: Ref<PuzzleStateKakurasu>;
}>();

const emits = defineEmits<{
  (e: "game-event", event_type: string, payload: object): void;
}>();

enum NonogramsCellStates {
  Empty = 0,
  Filled = 1,
  Crossed = 2,
  NUM_STATES,
}
const m = createStateMachinePuzzleModel<PuzzleStateNonograms>(props.state, NonogramsCellStates.NUM_STATES, (e, p) =>
  emits("game-event", e, p),
);

const borderConfig = {
  everyNthCol: { n: 5, style: { thickness: 2 } },
  everyNthRow: { n: 5, style: { thickness: 2 } },
  outer: { thickness: 1, borderClass: "bg-black" },
};
</script>
<template>
  <BoardContainer
    :rows="m.rows.value"
    :cols="m.cols.value"
    :scale="scale"
    :cell-size="12"
    :gutter-top="1"
    :gutter-left="1"
    class-game-cell="border-black"
    :model="m"
    :border-config="borderConfig"
  >
    <BoardBorders />
    <BoardInteraction />
    <BoardCells>
      <template v-slot:cell="{ row, col }">
        <div
          v-if="m.getCellState(row, col) === NonogramsCellStates.Filled"
          class="border-1 bg-black border-white h-full w-full"
        ></div>
        <div
          v-if="m.getCellState(row, col) === NonogramsCellStates.Crossed"
          class="bg-[url(/assets/kakurasu/cross.svg)] bg-contain w-full h-full"
        ></div>
      </template>
      <template v-slot:left="props">
        <div class="grid place-items-center">
          {{ m.state.value.row_sum[props.row] }}
        </div>
      </template>
      <template v-slot:top="props">
        <div class="grid place-items-center">
          {{ m.state.value.col_sum[props.col] }}
        </div>
      </template>
    </BoardCells>
  </BoardContainer>
</template>
