<script setup lang="ts">
import BoardContainer from "@/features/games.components/board.container.vue";
import BoardBorders from "@/features/games.components/board.borders.vue";
import BoardCells from "@/features/games.components/board.cellgrid.vue";
import BoardInteraction from "@/features/games.components/board.interaction.vue";
import { type createPuzzleInteractionBridge } from "@/features/games.composables/setupPuzzleInteractionBridge.ts";
import type { PuzzleState, NonogramMeta } from "@/services/game/engines/types.ts";
import { KakurasuCell } from "@/services/game/engines/translator.ts";
import { computed } from "vue";

const props = defineProps<{
  scale?: number;
  state: PuzzleState<NonogramMeta>;
  interact?: ReturnType<typeof createPuzzleInteractionBridge>;
}>();

const longestArray = (array: Array<Array<number>>) => array.reduce((longest, current) => {
  return current.length > longest.length ? current : longest;
}, []);

const gutter_left = computed(() => longestArray(props.state.definition.meta.row_hints).length  ?? 0);
const gutter_top = computed(() => longestArray(props.state.definition.meta.col_hints).length ?? 0);

const bind = props.interact?.getBridge();
const borderConfig = {
  outer: { thickness: 4, borderClass: "bg-black" },
  inner: { thickness: 1, borderClass: "bg-black" },
};
</script>
<template>
  <BoardContainer
    v-if="state.definition"
    :rows="state.definition.rows"
    :cols="state.definition.cols"
    :scale="scale"
    :gutter-top="gutter_top"
    :gutter-left="gutter_left"
    class-game-cell="border-black"
    :border-config="borderConfig"
  >
    <BoardBorders />
    <BoardInteraction v-if="interact" :bind="bind" />
    <BoardCells v-if="state">
      <template v-slot:cell="{ row, col }">
        <div
          v-if="state.board[row][col] === KakurasuCell.BLACK"
          class="border-1 bg-black border-white h-full w-full"
        ></div>
        <div
          v-if="state.board[row][col] === KakurasuCell.CROSS"
          class="bg-[url(/assets/kakurasu/cross.svg)] bg-contain w-full h-full"
        ></div>
      </template>
      <template v-slot:top="props">
        <div class="flex justify-center items-center text-gray-400">
          {{ state.definition.meta.col_hints[props.col][props.row - (gutter_top - state.definition.meta.col_hints[props.col].length)] ?? "" }}
        </div>
      </template>
      <template v-slot:left="props">
        <div class="flex justify-center items-center text-gray-400">
          {{ state.definition.meta.row_hints[props.row][props.col - (gutter_left - state.definition.meta.row_hints[props.row].length)] ?? "" }}
        </div>
      </template>
      <template v-slot:right="props">
        <div
          class="grid place-items-center"
        >
        </div>
      </template>
      <template v-slot:bottom="props">
        <div
          class="grid place-items-center"
        >
        </div>
      </template>
    </BoardCells>
  </BoardContainer>
</template>
