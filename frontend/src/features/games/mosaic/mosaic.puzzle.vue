<script setup lang="ts">
import BoardContainer from "@/features/games.components/board.container.vue";
import BoardBorders from "@/features/games.components/board.borders.vue";
import BoardCells from "@/features/games.components/board.cellgrid.vue";
import BoardInteraction from "@/features/games.components/board.interaction.vue";
import BoardBackground from "@/features/games.components/board.background.vue";
import { type createPuzzleInteractionBridge } from "@/features/games.composables/setupPuzzleInteractionBridge.ts";
import { check_violation_rule } from "@/utils.ts";
import { MosaicCell } from "@/services/game/engines/translator.ts";
import type { PuzzleState } from "@/services/game/engines/types.ts";

const props = defineProps<{
  scale?: number;
  state: PuzzleState;
  interact?: ReturnType<typeof createPuzzleInteractionBridge>;
}>();

const bind = props.interact?.getBridge();
const borderConfig = { outer: { thickness: 1, borderClass: "bg-gray-500" } };

// Helper to get the number clue from initial_state (if any)
const get_number_clue = (row: number, col: number): number | null => {
  const initial_value = props.state.definition.initial_state?.[row]?.[col];
  if (initial_value !== undefined && initial_value >= 0 && initial_value <= 9) {
    return initial_value;
  }
  return null;
};
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
    <BoardBackground class="bg-gray-500" />
    <BoardCells>
      <!-- prettier-ignore -->
      <template v-slot:cell="{ row, col }">
        <div
          class="w-full h-full select-none flex justify-center items-center text-2xl font-bold border border-gray-400"
          :class="[
            // Background colors for different cell states (from board)
            state.board[row][col] === MosaicCell.SHADED
              ? 'bg-black text-white'
              : state.board[row][col] === MosaicCell.CROSS
                ? 'bg-white text-black'
                : 'bg-gray-300 text-black',  // UNMARKED = gray

            // Violation highlighting overrides background
            check_violation_rule(state.violations, row, col, 'mosaic_shaded_count_violation') ? '!bg-red-300' : '',
          ]"
        >
          <!-- Always display number clue from initial_state if present -->
          <span v-if="get_number_clue(row, col) !== null" class="absolute">
            {{ get_number_clue(row, col) }}
          </span>
        </div>
      </template>
    </BoardCells>
  </BoardContainer>
</template>
