<script setup lang="ts">
import BoardContainer from "@/features/games.components/board.container.vue";
import BoardBorders from "@/features/games.components/board.borders.vue";
import BoardCells from "@/features/games.components/board.cellgrid.vue";
import BoardInteraction from "@/features/games.components/board.interaction.vue";
import BoardBackground from "@/features/games.components/board.background.vue";
import { type createPuzzleInteractionBridge } from "@/features/games.composables/setupPuzzleInteractionBridge.ts";
import { check_violation_rule } from "@/utils.ts";
import { MinesweeperCell } from "@/services/game/engines/translator.ts";
import type { PuzzleState } from "@/services/game/engines/types.ts";

const props = defineProps<{
  scale?: number;
  state: PuzzleState;
  interact?: ReturnType<typeof createPuzzleInteractionBridge>;
}>();

const bind = props.interact?.getBridge();
const borderConfig = { outer: { thickness: 1, borderClass: "bg-[#757575]" } };
</script>

<template>
  <BoardContainer
    v-if="state"
    :rows="state.definition.rows"
    :cols="state.definition.cols"
    :scale="scale"
    :gap="0"
    :border-config="borderConfig"
  >
    <BoardBorders />
    <BoardInteraction :bind="bind" />
    <BoardBackground class="bg-[#757575]" />
    <BoardCells>
      <!-- prettier-ignore -->
      <template v-slot:cell="{ row, col }">
        <div
          class="w-full h-full select-none flex justify-center items-center"
          :class="[{
            'bg-[url(/assets/minesweeper/unopened-square.svg)]': [MinesweeperCell.SAFE, MinesweeperCell.FLAG].includes(state.board[row][col])},
            check_violation_rule(state.violations, row, col, 'minesweeper_surrounding_flag_violation')
              ? 'bg-[url(/assets/minesweeper/cell-violation.svg)]'
              : 'bg-[url(/assets/minesweeper/cell-empty.svg)]'
          ]">
          <img v-if="state.board[row][col] === MinesweeperCell.ONE" src="/assets/minesweeper/number-1.svg" alt="1" class="bg-auto w-3/4 h-full" draggable="false" />
          <img v-if="state.board[row][col] === MinesweeperCell.TWO" src="/assets/minesweeper/number-2.svg" alt="2" class="bg-auto w-3/4 h-full" draggable="false" />
          <img v-if="state.board[row][col] === MinesweeperCell.THREE" src="/assets/minesweeper/number-3.svg" alt="3" class="bg-auto w-3/4 h-full" draggable="false" />
          <img v-if="state.board[row][col] === MinesweeperCell.FOUR" src="/assets/minesweeper/number-4.svg" alt="4" class="bg-auto w-3/4 h-full" draggable="false" />
          <img v-if="state.board[row][col] === MinesweeperCell.FIVE" src="/assets/minesweeper/number-5.svg" alt="5" class="bg-auto w-3/4 h-full" draggable="false" />
          <img v-if="state.board[row][col] === MinesweeperCell.SIX" src="/assets/minesweeper/number-6.svg" alt="6" class="bg-auto w-3/4 h-full" draggable="false" />
          <img v-if="state.board[row][col] === MinesweeperCell.SEVEN" src="/assets/minesweeper/number-7.svg" alt="7" class="bg-auto w-3/4 h-full" draggable="false" />
          <img v-if="state.board[row][col] === MinesweeperCell.EIGHT" src="/assets/minesweeper/number-8.svg" alt="8" class="bg-auto w-3/4 h-full" draggable="false" />

          <img v-if="state.board[row][col] === MinesweeperCell.UNMARKED" src="/assets/minesweeper/unopened-square.svg" alt="Unmarked" class="w-full h-full" />
          <img v-if="state.board[row][col] === MinesweeperCell.FLAG" src="/assets/minesweeper/flag.svg" alt="Flagged" class="w-full h-full" />
          <div v-if="state.board[row][col] === MinesweeperCell.SAFE" class="bg-lime-900 mask-[url(/assets/minesweeper/cell-safe.svg)] w-2/3 h-2/3 mask-center mask-no-repeat"></div>
        </div>
      </template>
    </BoardCells>
  </BoardContainer>
</template>
