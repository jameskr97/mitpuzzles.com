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

<style>
:root {
  --border-thickness: 10px;
  --border-thickness-bold: 30px;
}
</style>

<template>
  <GameGrid
    :rows="model.ROWS"
    :cols="model.COLS"
    :size="scale"
    @mouse-up="model.onCellClick($event.row, $event.col, $event.input_event)"
    @key-down="model.onCellKeyDown($event.row, $event.col, $event.input_event)"
    class="rounded border-5 bg-black"
    cell-class="nth-[3n]:not-last:mr-[5px] not-last:mr-[3px] w-full"
    row-class="nth-[3n]:not-last:mb-[5px] not-last:mb-[3px]"
  >
    <template v-slot:cell="{ row, col }">
      <div
        :style="{
          fontSize: '4cqmin',
        }"
        :class="{
          'border-red-500 border-5': model.isCellActive(row, col),
          'bg-slate-300': model.isSquareSelected(row, col) || model.isRowSelected(row) || model.isColSelected(col),
          'text-blue-600': model.canModifyCell(row, col),
        }"
        class="h-full bg-white leading-[0.8] grid grid-cols-1 place-items-center align-middle select-none"
      >
        <span>{{ model.getCellDisplay(row, col) }}</span>
      </div>
    </template>
  </GameGrid>
</template>
