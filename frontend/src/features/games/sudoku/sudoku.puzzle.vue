<script setup lang="ts">
import BoardBorders from "@/features/games.components/board.borders.vue";
import BoardContainer from "@/features/games.components/board.container.vue";
import BoardCells from "@/features/games.components/board.cellgrid.vue";
import BoardInteraction from "@/features/games.components/board.interaction.vue";
import { type createPuzzleInteractionBridge } from "@/features/games.composables/setupPuzzleInteractionBridge.ts";
import { computed } from "vue";
import type { PuzzleState } from "@/services/game/engines/types.ts";

////////////////////////////////////////////////////////////////////////
// Props + State
const props = defineProps<{
  scale?: number;
  state: PuzzleState;
  interact?: ReturnType<typeof createPuzzleInteractionBridge>;
}>();

function is_prefilled(row: number, col: number): boolean {
  return props.state.definition.initial_state[row][col] !== 0;
}

const bind = props.interact?.getBridge();
const render = props.interact?.getRenderBehaviors();

const T = 3;
const MAJOR = "bg-gray-500";
const borderConfig = computed(() => ({
  everyNthCol: { n: Math.sqrt(props.state.definition.cols), style: { thickness: T, borderClass: MAJOR } },
  everyNthRow: { n: Math.sqrt(props.state.definition.cols), style: { thickness: T, borderClass: MAJOR } },
  outer: { thickness: T, borderClass: MAJOR },
  inner: { borderClass: "bg-gray-400" },
}));
</script>

<template>
  <BoardContainer
    v-if="state"
    :cols="state.definition.cols"
    :rows="state.definition.rows"
    :scale="scale"
    :border-config="borderConfig"
  >
    <BoardBorders />
    <BoardInteraction :bind="bind" :bridge="interact" />
    <BoardCells>
      <template #cell="{ row, col }">
        <div
          v-if="render?.isCellVisible?.(row, col) ?? true"
          class="flex justify-center items-center h-full w-full overflow-hidden font-extrabold text-[60cqw] text-neutral-700"
          :class="render?.getCellClasses?.(row, col)"
        >
          <span v-if="render?.getCellContent">
            {{ render?.getCellContent(row, col) ?? "" }}
          </span>
          <div v-else-if="state.board[row][col] != 0">
            <span v-if="is_prefilled(row, col)">
              {{ state.board[row][col] }}
            </span>
            <span v-else-if="state.board[row][col] != 0">
              {{ state.board[row][col] }}
            </span>
          </div>
        </div>
      </template>
    </BoardCells>
  </BoardContainer>
</template>
