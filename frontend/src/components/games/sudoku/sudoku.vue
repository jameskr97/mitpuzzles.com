<script setup lang="ts">
import { remap } from "@/lib/util";
const SIDE_LENGTH = 9;

defineProps({
  scale: { type: Number, required: false, default: 1 },
});
</script>

<template>
  <div
    class="sudoku-board flex flex-col"
    :style="{
      '--scale': scale,
      '--font-size': remap([1, 5], [1.0, 3.5], scale),
    }"
  >
    <!-- Game Board -->
    <div class="flex flex-col border-4 w-max rounded">
      <div v-for="(_, iy) in SIDE_LENGTH" class="sudoku-row flex flex-row">
        <div
          v-for="(_, ix) in SIDE_LENGTH"
          class="sudoku-cell flex items-center justify-center"
        >
          <span>{{ iy * SIDE_LENGTH + ix }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.sudoku-board {
  --cell-size: 32px;
  --scale: 1;
  --border-thickness: 1px;
  --border-thickness-bold: 3px;
  --font-size: 1.5;
}

.sudoku-cell {
  height: calc(var(--cell-size) * var(--scale));
  width: calc(var(--cell-size) * var(--scale));
  border-right: var(--border-thickness) solid black;
  font-size: calc(var(--font-size) * 1rem);
  line-height: 0.7;
}

.sudoku-cell:nth-child(3n):not(:last-child) {
  border-right: var(--border-thickness-bold) solid black;
}

.sudoku-row {
  border-bottom: var(--border-thickness) solid black;
}

.sudoku-row:nth-child(3n):not(:last-child) {
  border-bottom: var(--border-thickness-bold) solid black;
}
</style>
