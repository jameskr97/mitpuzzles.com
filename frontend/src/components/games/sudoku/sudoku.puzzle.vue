<script setup lang="ts">
import { ModelSudokuPuzzle } from "@/components/games/sudoku/sudoku.model";
import GameGrid from "@/components/ui/game/game.grid.vue";

defineProps({
  scale: { type: Number, required: false, default: 1 },
});

const model = new ModelSudokuPuzzle();
</script>

<template>
  <GameGrid
    :rows="model.ROWS"
    :cols="model.COLS"
    :size="scale"
    @mouse-up="model.onCellClick($event.row, $event.col, $event.input_event)"
    @key-down="model.onCellKeyDown($event.row, $event.col, $event.input_event)"
    class="rounded border-5 bg-black"
    cell-style="nth-[3n]:not-last:mr-(--border-thickness-bold) mr-(--border-thickness) bg-white"
    row-style="nth-[3n]:not-last:mb-(--border-thickness-bold) mb-(--border-thickness)"
  >
    <template v-slot:cell="{ row, col }">
      <div
        :style="{
          fontSize: scale + 'rem',
        }"
        :class="{
          'border-cyan-800 border-2': model.isCellActive(row, col),
          'bg-slate-300': model.isSquareSelected(row, col) || model.isRowSelected(row) || model.isColSelected(col),
          'text-blue-600': model.canModifyCell(row, col),
        }"
        class="h-full leading-[0.8] grid grid-cols-1 place-items-center align-middle select-none"
      >
        <span>{{ model.getCellDisplay(row, col) }}</span>
      </div>
    </template>
  </GameGrid>
</template>

<style>
:root {
  --border-thickness: 1px;
  --border-thickness-bold: 3px;
}
</style>
