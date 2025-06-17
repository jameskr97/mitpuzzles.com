<script setup lang="ts">
import BoardContainer from "@/features/games.components/board.container.vue";
import BoardBorders from "@/features/games.components/board.borders.vue";
import BoardCells from "@/features/games.components/board.cellgrid.vue";
import BoardInteraction from "@/features/games.components/board.interaction.vue";
import type { PuzzleStateTents } from "@/services/states.ts";
import { type createPuzzleInteractionBridge } from "@/features/games.composables/setupPuzzleInteractionBridge.ts";
import { check_violation_rule } from "@/utils.ts";

const props = defineProps<{
  scale?: number;
  state: PuzzleStateTents;
  interact?: ReturnType<typeof createPuzzleInteractionBridge>;
}>();

enum TentCellStates {
  Empty = 0,
  Tree,
  Tent,
  Green,
  NUM_STATES,
}
const bind = props.interact?.getBridge();
const borderConfig = {
  outer: { thickness: 1, borderClass: "bg-black" },
  inner: { thickness: 1, borderClass: "bg-black" }
};
</script>

<template>
  <BoardContainer
    v-if="state"
    :rows="state.rows"
    :cols="state.cols"
    :gutter-top="1"
    :gutter-left="1"
    :scale="scale"
    :border-config="borderConfig"
  >
    <BoardBorders />
    <BoardInteraction :bind="bind" />
    <BoardCells>
      <!-- prettier-ignore -->
      <template v-slot:cell="{ row, col }">
      <div class="w-full h-full">
        <img
          v-if="state.board[row * state.cols + col] === TentCellStates.Tent"
          src="/assets/tents/tent.svg"
          alt="Tent"
          class="w-full h-full"
          :class="check_violation_rule(state.violations!, row, col, 'tents_intersecting') ? 'bg-red-300' : 'bg-green-300'"
        />
        <img v-else-if="state.board[row * state.cols + col] === TentCellStates.Tree" src="/assets/tents/tree.svg" alt="Tree" class="w-full h-full bg-green-300" />
        <div v-else-if="state.board[row * state.cols + col] === TentCellStates.Green" class="w-full h-full bg-green-300" />
      </div>
    </template>

      <template v-slot:top="{ col }">
        <div
          class="font-bold flex justify-center items-center h-full w-full"
          :class="{
            'text-red-500': check_violation_rule(state.violations!, -1, col, 'tent_count_col_mismatch'),
          }"
        >
          {{ state.col_counts[col] }}
        </div>
      </template>

      <template v-slot:left="{ row }">
        <div
          class="grid h-full font-bold text-end items-center justify-center"
          :class="{
            'text-red-500': check_violation_rule(state.violations!, row, -1, 'tent_count_row_mismatch'),
          }"
        >
          {{ state.row_counts[row] }}
        </div>
      </template>
    </BoardCells>
  </BoardContainer>
</template>
