<script setup lang="ts">
import BoardContainer from "@/features/games.components/board.container.vue";
import BoardBorders from "@/features/games.components/board.borders.vue";
import BoardCells from "@/features/games.components/board.cellgrid.vue";
import BoardInteraction from "@/features/games.components/board.interaction.vue";
import { type createPuzzleInteractionBridge } from "@/features/games.composables/setupPuzzleInteractionBridge.ts";
import { check_violation_rule } from "@/utils.ts";
import type { PuzzleState, TentsMeta } from "@/services/game/engines/types.ts";
import { TentsCell } from "@/services/game/engines/translator.ts";

const props = defineProps<{
  scale?: number;
  state: PuzzleState<TentsMeta>;
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
  inner: { thickness: 1, borderClass: "bg-black" },
};
</script>

<template>
  <BoardContainer
    v-if="state"
    :rows="state.definition.rows"
    :cols="state.definition.cols"
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
            v-if="state.board[row][col] === TentsCell.TENT"
            src="/assets/tents/tent.svg"
            alt="Tent"
            class="w-full h-full"
            :class="check_violation_rule(state.violations!, row, col, 'tents_intersecting') ? 'bg-red-300' : 'bg-green-300'"
          />
          <img v-else-if="state.board[row][col] === TentsCell.TREE" src="/assets/tents/tree.svg" alt="Tree"
               class="w-full h-full bg-green-300" />
          <div v-else-if="state.board[row][col] === TentsCell.GREEN" class="w-full h-full bg-green-300" />
        </div>
      </template>

      <template v-slot:top="{ col }">
        <div
          class="font-bold flex justify-center items-center h-full w-full"
          :class="{
            'text-red-500': check_violation_rule(state.violations!, -1, col, 'line_sum_col_exceeded'),
          }"
        >
          {{ state.definition.meta!.col_tent_counts[col] }}
        </div>
      </template>

      <template v-slot:left="{ row }">
        <div
          class="grid h-full font-bold text-end items-center justify-center"
          :class="{
            'text-red-500': check_violation_rule(state.violations!, row, -1, 'line_sum_row_exceeded'),
          }"
        >
          {{ state.definition.meta!.row_tent_counts[row] }}
        </div>
      </template>
    </BoardCells>
  </BoardContainer>
</template>
