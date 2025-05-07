<script setup lang="ts">
import BoardContainer from "@/features/games/components/board.container.vue";
import BoardBorders from "@/features/games/components/board.borders.vue";
import BoardCells from "@/features/games/components/board.cellgrid.vue";
import BoardInteraction from "@/features/games/components/board.interaction.vue";
import BoardBackground from "@/features/games/components/board.background.vue";
import { type Ref } from "vue";
import { createStateMachinePuzzleModel } from "@/features/games/composables/PuzzleModelBase";
import type { PuzzleStateMinesweeper } from "@/services/states.ts";

const props = defineProps<{
  scale?: number;
  state: Ref<PuzzleStateMinesweeper>;
}>();

const emits = defineEmits<{
  (e: "game-event", event_type: string, payload: object): void;
}>();

enum MinesweeperCellStates {
  Unmarked = 10,
  Flagged = 11,
  Safe = 12,
  NUM_STATES = 3,
}

const m = createStateMachinePuzzleModel<PuzzleStateMinesweeper>(
  props.state,
  MinesweeperCellStates.NUM_STATES,
  (e, p) => emits("game-event", e, p),
  {
    allowedStates: [MinesweeperCellStates.Unmarked, MinesweeperCellStates.Flagged, MinesweeperCellStates.Safe],
    canModifyCell(row: number, col: number, state: PuzzleStateMinesweeper) {
      return state.board_initial[row * state.cols + col] === "_";
    },
  },
);

const borderConfig = {
  outer: { thickness: 1, borderClass: "bg-[#757575]" },
};
</script>

<template>
  <BoardContainer
    :rows="m.rows.value"
    :cols="m.cols.value"
    :scale="scale"
    :gap="0"
    :border-config="borderConfig"
    :model="m"
  >
    <BoardBorders />
    <BoardInteraction />
    <BoardBackground class="bg-[#757575]" />
    <BoardCells>
      <!-- prettier-ignore -->
      <template v-slot:cell="props">
        <div class="w-full h-full select-none bg-[url(/assets/minesweeper/cell-empty.svg)]">
          <img v-if="m.getCellState(props.row, props.col) === 0" src="/assets/minesweeper/cell-empty.svg" alt="1" class="bg-auto w-full h-full" draggable="false" />
          <img v-if="m.getCellState(props.row, props.col) === 1" src="/assets/minesweeper/number-1.svg" alt="1" class="bg-auto w-full h-full" draggable="false" />
          <img v-if="m.getCellState(props.row, props.col) === 2" src="/assets/minesweeper/number-2.svg" alt="2" class="bg-auto w-full h-full" draggable="false" />
          <img v-if="m.getCellState(props.row, props.col) === 3" src="/assets/minesweeper/number-3.svg" alt="3" class="bg-auto w-full h-full" draggable="false" />
          <img v-if="m.getCellState(props.row, props.col) === 4" src="/assets/minesweeper/number-4.svg" alt="4" class="bg-auto w-full h-full" draggable="false" />
          <img v-if="m.getCellState(props.row, props.col) === 5" src="/assets/minesweeper/number-5.svg" alt="5" class="bg-auto w-full h-full" draggable="false" />
          <img v-if="m.getCellState(props.row, props.col) === 6" src="/assets/minesweeper/number-6.svg" alt="6" class="bg-auto w-full h-full" draggable="false" />
          <img v-if="m.getCellState(props.row, props.col) === 7" src="/assets/minesweeper/number-7.svg" alt="7" class="bg-auto w-full h-full" draggable="false" />
          <img v-if="m.getCellState(props.row, props.col) === 8" src="/assets/minesweeper/number-8.svg" alt="8" class="bg-auto w-full h-full" draggable="false" />

          <img v-if="m.getCellState(props.row, props.col) === MinesweeperCellStates.Unmarked" src="/assets/minesweeper/unopened-square.svg" alt="Unmarked" class="w-full h-full" />
          <img v-if="m.getCellState(props.row, props.col) === MinesweeperCellStates.Flagged" src="/assets/minesweeper/flag.svg" alt="Flagged" class="w-full h-full bg-[url(/assets/minesweeper/unopened-square.svg)]" />
          <img v-if="m.getCellState(props.row, props.col) === MinesweeperCellStates.Safe" src="/assets/minesweeper/cell-safe.svg" alt="Safe" class="w-full h-full bg-[url(/assets/minesweeper/unopened-square.svg)]" />
  <!--        <img v-if="model.isCellInDangerZone(props.row, props.col)" src="/assets/minesweeper/cell-empty.svg" alt="Danger Zone" class="w-full h-full" />-->
        </div>
      </template>
    </BoardCells>
  </BoardContainer>
</template>
