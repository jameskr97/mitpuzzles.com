<script setup lang="ts">
import BoardContainer from "@/features/games.components/board.container.vue";
import BoardBorders from "@/features/games.components/board.borders.vue";
import BoardCells from "@/features/games.components/board.cellgrid.vue";
import BoardInteraction from "@/features/games.components/board.interaction.vue";
import { type createPuzzleInteractionBridge } from "@/features/games.composables/setupPuzzleInteractionBridge.ts";
import { check_violation_rule } from "@/utils.ts";
import type { PuzzleState, KakurasuMeta } from "@/services/game/engines/types.ts";
import { KakurasuCell } from "@/services/game/engines/translator.ts";

const props = defineProps<{
  scale?: number;
  state: PuzzleState<KakurasuMeta>;
  interact?: ReturnType<typeof createPuzzleInteractionBridge>;
}>();
enum KakurasuCellStates {
  Empty = 0,
  Filled = 1,
  Crossed = 2,
  NUM_STATES,
}

const bind = props.interact?.getBridge();
const borderConfig = {
  outer: { thickness: 1, borderClass: "bg-black" },
  inner: { thickness: 1, borderClass: "bg-black" },
};
</script>
<template>
  <BoardContainer
    v-if="state.definition"
    :rows="state.definition.rows"
    :cols="state.definition.cols"
    :scale="scale"
    :gutter-top="1"
    :gutter-left="1"
    :gutter-right="1"
    :gutter-bottom="1"
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
          {{ props.col + 1 }}
        </div>
      </template>
      <template v-slot:left="props">
        <div class="flex justify-center items-center text-gray-400">
          {{ props.row + 1 }}
        </div>
      </template>
      <template v-slot:right="props">
        <div
          class="grid place-items-center"
          :class="
            check_violation_rule(state.violations!, props.row, -1, 'line_sum_row_exceeded')
              ? 'text-red-500'
              : 'text-blue-500'
          "
        >
          {{ state.definition.meta.row_sums[props.row] }}
        </div>
      </template>
      <template v-slot:bottom="props">
        <div
          class="grid place-items-center"
          :class="
            check_violation_rule(state.violations!, -1, props.col, 'line_sum_col_exceeded')
              ? 'text-red-500'
              : 'text-blue-500'
          "
        >
          <span>{{ state.definition.meta.col_sums[props.col] }}</span>
        </div>
      </template>
    </BoardCells>
  </BoardContainer>
</template>
