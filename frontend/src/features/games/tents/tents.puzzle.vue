<script setup lang="ts">
import BoardContainer from "@/features/games/components/board.container.vue";
import BoardBorders from "@/features/games/components/board.borders.vue";
import BoardCells from "@/features/games/components/board.cellgrid.vue";
import BoardInteraction from "@/features/games/components/board.interaction.vue";
import { type Ref } from "vue";
import { createStateMachinePuzzleModel } from "@/features/games/composables/PuzzleModelBase.ts";
import type { PuzzleStateTents } from "@/services/states.ts";
import { PuzzleModelOps } from "@/features/games/composables/PuzzleModelOps.ts";

const props = defineProps<{
  scale?: number;
  state: Ref<any>;
}>();

const emits = defineEmits<{
  (e: "game-event", event_type: string, payload: object): void;
}>();

enum TentCellStates {
  Empty = 0,
  Tree,
  Tent,
  Green,
  NUM_STATES,
}

const m = createStateMachinePuzzleModel<PuzzleStateTents>(
  props.state,
  TentCellStates.NUM_STATES,
  (e, p) => emits("game-event", e, p),
  {
    allowedStates: [TentCellStates.Empty, TentCellStates.Tent, TentCellStates.Green],
    canModifyCell(row: number, col: number, state: PuzzleStateTents) {
      return state.board[row * state.cols + col] !== TentCellStates.Tree;
    },
    onLeftGutterCellClick(row: number, _col: number, state: PuzzleStateTents) {
      PuzzleModelOps.changeLineState(true, row, state, TentCellStates.Empty, TentCellStates.Green);
    },
    onTopGutterCellClick(_row :number, col: number, state: PuzzleStateTents) {
      PuzzleModelOps.changeLineState(false, col, state, TentCellStates.Empty, TentCellStates.Green);
    },
  },
);

const borderConfig = {
  outer: { thickness: 1, borderClass: "bg-black" },
};
</script>

<template>
  <BoardContainer
    :rows="m.rows.value"
    :cols="m.cols.value"
    :gutter-top="1"
    :gutter-left="1"
    :scale="scale"
    :model="m"
    :border-config="borderConfig"
  >
    <BoardBorders />
    <BoardInteraction />
    <BoardCells>
      <!-- prettier-ignore -->
      <template v-slot:cell="{ row, col }">
      <div class="w-full h-full">
        <img v-if="m.getCellState(row, col) === TentCellStates.Tent" src="/assets/tents/tent.svg" alt="Tent" class="w-full h-full bg-green-300" />
        <img v-else-if="m.getCellState(row, col) === TentCellStates.Tree" src="/assets/tents/tree.svg" alt="Tree" class="w-full h-full bg-green-300" />
        <div v-else-if="m.getCellState(row, col) === TentCellStates.Green" class="w-full h-full bg-green-300" />
      </div>
    </template>

      <template v-slot:top="{ col }">
        <div class="font-bold flex justify-center items-center h-full w-full">
          {{ m.state.value.col_counts[col] }}
        </div>
      </template>

      <template v-slot:left="{ row }">
        <div class="grid h-full font-bold text-end items-center justify-center">
          {{ m.state.value.row_counts[row] }}
        </div>
      </template>
    </BoardCells>
  </BoardContainer>
</template>
