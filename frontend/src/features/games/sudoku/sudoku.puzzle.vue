<script setup lang="ts">
import { ModelSudokuPuzzle } from "@/features/games/sudoku/sudoku.model";
import GameGrid from "@/components/game/game.grid.vue";
import { reactive } from "vue";

const props = defineProps<{
  scale?: number;
  state: any;
}>();

const emits = defineEmits<{
  (e: "game-event", event_type: string, payload: object): void;
}>();
const model = reactive(
  new ModelSudokuPuzzle(props.state, (event: string, payload: object) => {
    emits("game-event", event, payload);
  }),
);
</script>

<template>
  <GameGrid
    :rows="model.ROWS"
    :cols="model.COLS"
    :scale="scale"
    :cell-size="7"
    @mouse-up="model.onCellClick($event.row, $event.col, $event.input_event)"
    @key-down="model.onCellKeyDown($event.row, $event.col, $event.input_event)"
  >
    <template v-slot:cell="{ row, col }">
      <div
        v-if="model.getCellDisplay(row, col) !== null"
        class="flex justify-center items-center h-full w-full"
        :class="{
          'border-red-500 border-[1px]': model.isCellActive(row, col),
          'bg-slate-300': model.isSquareSelected(row, col) || model.isRowSelected(row) || model.isColSelected(col),
          'text-blue-600': model.canModifyCell(row, col),
        }"
      >
        {{ model.getCellDisplay(row, col) }}
      </div>
    </template>
  </GameGrid>
</template>
