<script setup lang="ts">
import type PuzzleMinesweeper from "@/model/PuzzleMinesweeper";
import { ModelMinesweeperPuzzle } from "@/components/games/minesweeper/minesweeper.model";
import { reactive } from "vue";

////////////////////////////////////////////////////////////////////////////////
// Props + Events
const props = withDefaults(
  defineProps<{
    puzzle: PuzzleMinesweeper;
    scale?: number;
  }>(),
  { scale: 2 }
);

const model = reactive<ModelMinesweeperPuzzle>(
    new ModelMinesweeperPuzzle(props.puzzle.rows, props.puzzle.cols, props.puzzle.board)
);
</script>

<template>
  <!-- Grid container for the game board itself -->
  <div class="flex">
    <div class="minesweeper-board w-max flex-col" :style="{ '--scale': scale }">
      <!-- Each Row for the board -->
      <div v-for="(_, row) in puzzle.rows" class="flex flex-row">
        <div
          v-for="(_, col) in puzzle.cols"
          :key="'m' + row + '_' + col"
          :class="'cell w-full ' + model.getCellClass(row, col)"
          @mousedown.prevent="model.onCellMouseDown(row, col)"
          @mouseup.prevent="model.onCellMouseUp(row, col)"
          @mouseenter.prevent="model.onCellMouseEnter(row, col)"
          @mouseleave.prevent
          @click.prevent
          @contextmenu.prevent
        ></div>
      </div>
    </div>
  </div>
</template>

<!-- prettier-ignore -->
<style scoped>
.minesweeper-board {
  --cell-size: 16px;
  --scale: 1;
}

.cell {
  height: calc(var(--cell-size) * var(--scale));
  width: calc(var(--cell-size) * var(--scale));
  background-size: contain;
}

/* All Minesweeper Specific Cells */
.cell-unrevealed    { background-image: url("/assets/minesweeper/unopened-square.svg"); background-size: 100%; }
.cell-00            { background-image: url("/assets/minesweeper/number-0.svg"); }
.cell-01            { background-image: url("/assets/minesweeper/number-1.svg"),    url("/assets/minesweeper/number-0.svg"); }
.cell-02            { background-image: url("/assets/minesweeper/number-2.svg"),    url("/assets/minesweeper/number-0.svg"); }
.cell-03            { background-image: url("/assets/minesweeper/number-3.svg"),    url("/assets/minesweeper/number-0.svg"); }
.cell-04            { background-image: url("/assets/minesweeper/number-4.svg"),    url("/assets/minesweeper/number-0.svg"); }
.cell-05            { background-image: url("/assets/minesweeper/number-5.svg"),    url("/assets/minesweeper/number-0.svg"); }
.cell-06            { background-image: url("/assets/minesweeper/number-6.svg"),    url("/assets/minesweeper/number-0.svg"); }
.cell-07            { background-image: url("/assets/minesweeper/number-7.svg"),    url("/assets/minesweeper/number-0.svg"); }
.cell-08            { background-image: url("/assets/minesweeper/number-8.svg"),    url("/assets/minesweeper/number-0.svg"); }
.cell-mine          { background-image: url("/assets/minesweeper/bomb.svg"),        url("/assets/minesweeper/number-0.svg"); }
.cell-mine-explode  { background-image: url("/assets/minesweeper/bomb.svg"),        url("/assets/minesweeper/bomb-explode.svg"); }
.cell-flag          { background-image: url("/assets/minesweeper/flag.svg"),        url("/assets/minesweeper/unopened-square.svg"); }
.cell-flag-incorrect   {
  background-image:
    url("/assets/minesweeper/flag-missed.svg"),
    url("/assets/minesweeper/flag.svg"),
    url("/assets/minesweeper/unopened-square.svg");
  background-size: calc(var(--cell-size) * calc(var(--scale) - 0.5)), contain, contain;
  background-position: center, center, center;
  background-repeat: no-repeat;
}
</style>
