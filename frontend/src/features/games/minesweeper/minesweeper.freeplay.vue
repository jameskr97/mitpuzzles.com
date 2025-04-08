<script setup lang="ts">
import GameLayout from "@/components/layout/game.layout.vue";
import MinesweeperPuzzle from "@/features/games/minesweeper/minesweeper.puzzle.vue";
import { ref } from "vue";
import { useCurrentPuzzle } from "@/composables";

const { state, push_event } = await useCurrentPuzzle();
function on_game_event(event_type: string, payload: object) {
  push_event(event_type, payload);
}
</script>

<!-- prettier-ignore -->
<style scoped>
.cell {
  height: calc(16px * 1);
  width: calc(16px * 1);
  background-size: contain;
  display: inline-block;
}

/* All Minesweeper Specific Cells */
.cell-empty       { background-image: url("/assets/minesweeper/cell-safe.svg"); }
.cell-flag        { background-image: url("/assets/minesweeper/flag.svg"), url("/assets/minesweeper/unopened-square.svg"); }
.cell-unrevealed  { background-image: url("/assets/minesweeper/unopened-square.svg");}
</style>

<template>
  <div>
    <p class="text-center text-2xl">Minesweeper</p>
    <div class="divider m-0"></div>
    <GameLayout>
      <template #instructions>
        <li>
          Your goal is to correctly mark each of the cells (<i class="cell cell-unrevealed"></i>) as safe (<i
            class="cell w-full cell-empty inline-block"
          ></i
          >) or flagged (<i class="cell cell-flag"></i>).
        </li>
        <li>Click the cell cycle through the states.</li>
        <li>
          Once you have marked all the cells, click the <span class="text-green-500">Submit</span> button to check your
          solution.
        </li>
        <li>Want to start over? Click <span class="text-red-500">Clear</span> to reset the board.</li>
        <li>
          Want to try a different puzzle? Click the <span class="text-blue-500">New Puzzles</span> button to get a new
          puzzle.
        </li>
      </template>

      <template v-slot:default="props">
        <MinesweeperPuzzle :state="state" :scale="props.scale" @game-event="on_game_event" />
      </template>
    </GameLayout>
  </div>
</template>
