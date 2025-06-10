<script setup lang="ts">
import BoardContainer from "@/features/games.components/board.container.vue";
import BoardBorders from "@/features/games.components/board.borders.vue";
import BoardCells from "@/features/games.components/board.cellgrid.vue";
import BoardInteraction from "@/features/games.components/board.interaction.vue";
import BoardBackground from "@/features/games.components/board.background.vue";
import { type createPuzzleInteractionBridge } from "@/features/games.composables/setupPuzzleInteractionBridge.ts";
import type { PuzzleStateMinesweeper } from "@/services/states.ts";
import { check_violation_rule } from "@/utils.ts";

const props = defineProps<{
  scale?: number;
  state: PuzzleStateMinesweeper;
  interact?: ReturnType<typeof createPuzzleInteractionBridge>;
}>();

enum MinesweeperCellStates {
  Unmarked = 9,
  Flagged = 10,
  Safe = 11,
  NUM_STATES = 3,
}
const bind = props.interact?.getBridge();
const borderConfig = { outer: { thickness: 1, borderClass: "bg-[#757575]" } };
</script>

<template>
  <BoardContainer :rows="state.rows" :cols="state.cols" :scale="scale" :gap="0" :border-config="borderConfig">
    <BoardBorders />
    <BoardInteraction :bind="bind" />
    <BoardBackground class="bg-[#757575]" />
    <BoardCells>
      <!-- prettier-ignore -->
      <template v-slot:cell="{ row, col }">
        <div
          class="w-full h-full select-none"
          :class="{
            'bg-[url(/assets/minesweeper/cell-empty.svg)]': !check_violation_rule(state.violations!, row, col, 'minesweeper_surrounding_flag_violation'),
            'bg-[url(/assets/minesweeper/cell-violation.svg)]': check_violation_rule(state.violations!, row, col, 'minesweeper_surrounding_flag_violation'),
          }">
          <img v-if="state.board[row * state.cols + col] === 0" src="/assets/minesweeper/cell-empty.svg" alt="1" class="bg-auto w-full h-full" draggable="false" />
          <img v-if="state.board[row * state.cols + col] === 1" src="/assets/minesweeper/number-1.svg" alt="1" class="bg-auto w-full h-full" draggable="false" />
          <img v-if="state.board[row * state.cols + col] === 2" src="/assets/minesweeper/number-2.svg" alt="2" class="bg-auto w-full h-full" draggable="false" />
          <img v-if="state.board[row * state.cols + col] === 3" src="/assets/minesweeper/number-3.svg" alt="3" class="bg-auto w-full h-full" draggable="false" />
          <img v-if="state.board[row * state.cols + col] === 4" src="/assets/minesweeper/number-4.svg" alt="4" class="bg-auto w-full h-full" draggable="false" />
          <img v-if="state.board[row * state.cols + col] === 5" src="/assets/minesweeper/number-5.svg" alt="5" class="bg-auto w-full h-full" draggable="false" />
          <img v-if="state.board[row * state.cols + col] === 6" src="/assets/minesweeper/number-6.svg" alt="6" class="bg-auto w-full h-full" draggable="false" />
          <img v-if="state.board[row * state.cols + col] === 7" src="/assets/minesweeper/number-7.svg" alt="7" class="bg-auto w-full h-full" draggable="false" />
          <img v-if="state.board[row * state.cols + col] === 8" src="/assets/minesweeper/number-8.svg" alt="8" class="bg-auto w-full h-full" draggable="false" />

          <img v-if="state.board[row * state.cols + col] === MinesweeperCellStates.Unmarked" src="/assets/minesweeper/unopened-square.svg" alt="Unmarked" class="w-full h-full" />
          <img v-if="state.board[row * state.cols + col] === MinesweeperCellStates.Flagged" src="/assets/minesweeper/flag.svg" alt="Flagged" class="w-full h-full bg-[url(/assets/minesweeper/unopened-square.svg)]" />
          <img v-if="state.board[row * state.cols + col] === MinesweeperCellStates.Safe" src="/assets/minesweeper/cell-safe.svg" alt="Safe" class="w-full h-full bg-[url(/assets/minesweeper/unopened-square.svg)]" />
        </div>
      </template>
    </BoardCells>
  </BoardContainer>
</template>
