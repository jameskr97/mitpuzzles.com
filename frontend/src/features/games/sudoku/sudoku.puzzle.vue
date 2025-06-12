<script setup lang="ts">
import BoardBorders from "@/features/games.components/board.borders.vue";
import BoardContainer from "@/features/games.components/board.container.vue";
import BoardCells from "@/features/games.components/board.cellgrid.vue";
import BoardInteraction from "@/features/games.components/board.interaction.vue";
import { type createPuzzleInteractionBridge } from "@/features/games.composables/setupPuzzleInteractionBridge.ts";
import { computed } from "vue";
import type { PuzzleStateSudoku } from "@/services/states.ts"; ////////////////////////////////////////////////////////////////////////

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

const bind = props.interact?.getBridge(false);
const render = props.interact?.getRenderBehaviors();

const borderConfig = computed(() => ({
  everyNthCol: { n: Math.sqrt(props.state.cols), style: { thickness: 2 } },
  everyNthRow: { n: Math.sqrt(props.state.cols), style: { thickness: 2 } },
  outer: { thickness: 2, borderClass: "bg-black" },
}));
</script>

<template>
  <BoardContainer v-if="state" :cols="state.cols" :rows="state.rows" :scale="scale" :border-config="borderConfig">
    <BoardBorders />
    <BoardInteraction :bind="bind" />
    <BoardCells>
      <template #cell="{ row, col }">
        <div
          v-if="render?.isCellVisible?.(row, col) ?? true"
          class="flex justify-center items-center h-full w-full overflow-hidden"
          :class="render?.getCellClasses?.(row, col)"
        >
          <span v-if="render?.getCellContent">
            {{ render?.getCellContent(row, col) ?? "" }}
          </span>
          <div v-else>
            <span v-if="is_prefilled(row, col)">
              {{ state.board[row * state.cols + col] }}
            </span>
            <span v-else-if="state.board[row * state.cols + col] != 0">
              {{ state.board[row * state.cols + col] }}
            </span>
          </div>
        </div>
      </template>
    </BoardCells>
  </BoardContainer>
</template>
