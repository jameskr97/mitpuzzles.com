<script setup lang="ts">
import BoardBorders from "@/features/games.components/board.borders.vue";
import BoardContainer from "@/features/games.components/board.container.vue";
import BoardCells from "@/features/games.components/board.cellgrid.vue";
import BoardInteraction from "@/features/games.components/board.interaction.vue";
import { type createPuzzleInteractionBridge } from "@/features/games.composables/setupPuzzleInteractionBridge.ts";
import { computed } from "vue";
import type { PuzzleStateSudoku } from "@/services/states.ts";
import { createSudokuBehavior } from "@/features/games.composables/useSudokuHighlight.ts";
import { check_violation_rule } from "@/utils.ts";

////////////////////////////////////////////////////////////////////////
// Props + State
const props = defineProps<{
  scale?: number;
  state: PuzzleStateSudoku;
  interact?: ReturnType<typeof createPuzzleInteractionBridge>;
}>();

function is_prefilled(row: number, col: number): boolean {
  const index = row * props.state.cols + col;
  return props.state.board_initial[index] !== 0;
}

////////////////////////////////////////////////////////////////////////
// Game Specific Logic
const highlight = props.interact?.addInputBehaviour(createSudokuBehavior);

const bind = props.interact?.getBridge(false);

const borderConfig = computed(() => ({
  everyNthCol: { n: Math.sqrt(props.state.cols), style: { thickness: 2 } },
  everyNthRow: { n: Math.sqrt(props.state.cols), style: { thickness: 2 } },
  outer: { thickness: 2, borderClass: "bg-black" },
}));
</script>

<template>
  <BoardContainer :cols="state.cols" :rows="state.rows" :scale="scale" :border-config="borderConfig">
    <BoardBorders />
    <BoardInteraction :bind="bind" />
    <BoardCells>
      <template #cell="{ row, col }">
        <div
          class="flex justify-center items-center h-full w-full"
          :class="{
            'border-blue-500 border-[0.5px]': highlight?.isCellActive(row, col),
            'border-red-500! border-[0.5px]': check_violation_rule(state.violations!, row, col, [
              'row_duplicate_violation',
              'col_duplicate_violation',
              'box_duplicate_violation',
            ]),
            'bg-slate-300': highlight?.shouldHighlightCell(row, col),
            'text-blue-600': !is_prefilled(row, col),
          }"
        >
          <span v-if="is_prefilled(row, col)">
            {{ state.board[row * state.cols + col] }}
          </span>
          <span v-else-if="state.board[row * state.cols + col] != 0">
            {{ state.board[row * state.cols + col] }}
          </span>
        </div>
      </template>
    </BoardCells>
  </BoardContainer>
</template>
