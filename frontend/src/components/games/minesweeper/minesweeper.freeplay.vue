<script setup lang="ts">
import GameLayout from "@/components/ui/layout/game.layout.vue";
import MinesweeperPuzzle from "@/components/games/minesweeper/minesweeper.puzzle.vue";
import { ref } from "vue";
import { useCurrentPuzzle } from "@/composables";

const { state, reset, is_solved, push_event } = await useCurrentPuzzle();

const message = ref();
const hash = ref("");
const display_unsolved = ref(false);
function on_game_event(event_type: string, payload: object) {
  push_event(event_type, payload);
}

// function on_new_puzzle() {
//   reset_view();
//   ms.fetchPuzzle(true);
// }

// function check_game_solved() {
//   if (hash.value === ms.puzzle.solution_hash) {
//     message.value = "Game Solved!";
//     ms.mark_solved();
//   } else {
//     display_unsolved.value = true;
//     message.value = "Game not solved yet.";
//   }
// }
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
        <MinesweeperPuzzle
          :class="[
            'bg-gray-600 rounded-md border-5 mx-auto max-w-fit',
            is_solved ? 'border-green-500' : '',
            display_unsolved ? 'border-red-500' : '',
          ]"
          :state="state"
          :scale="props.scale"
          @game-event="on_game_event"
        />

        <div class="flex flex-col items-center">
          <div v-if="message" role="alert" class="alert alert-warning mb-2 rounded-2xl text-xl text-center w-64">
            {{ message }}
          </div>
        </div>
      </template>
    </GameLayout>
  </div>
</template>
