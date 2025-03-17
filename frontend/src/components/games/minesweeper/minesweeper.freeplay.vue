<script setup lang="ts">
import GameLayout from "@/components/ui/layout/game.layout.vue";
import MinesweeperPuzzle from "@/components/games/minesweeper/minesweeper.puzzle.vue";
import { useMinesweeperStore } from "@/store/game";
import { sha256 } from "@/lib/util";
import { ref, watchEffect } from "vue";

const message = ref();
const hash = ref("");
const display_unsolved = ref(false);

// TODO(james): We only support 7x7 boards with this line 💀 fix that.
const ms = useMinesweeperStore(7, 7);
await ms.fetchPuzzle();

function reset_view() {
  message.value = "";
  display_unsolved.value = false;
}

function on_game_event(event_type: string, payload: object) {
  if (ms.puzzle.completed_at !== null) return;
  reset_view();
  ms.record_event(event_type, payload);
}

function on_new_puzzle() {
  reset_view();
  ms.fetchPuzzle(true);
}

function check_game_solved() {
  console.log(ms.puzzle.solution_hash);
  if (hash.value === ms.puzzle.solution_hash) {
    message.value = "Game Solved!";
    ms.mark_solved();
  } else {
    display_unsolved.value = true;
    message.value = "Game not solved yet.";
  }
}

watchEffect(async () => {
  if (!ms.puzzle) return;
  hash.value = await sha256(ms.validation);
  if (hash.value === ms.puzzle.solution_hash)
    ms.record_event("game_solved", {});
});
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
    <p class="text-center text-2xl">Minesweeper Logic Puzzle</p>
    <div class="divider m-0"></div>
    <GameLayout :store="ms" :maxScale="3">
      <template #left>
        <div class="flex flex-col md:w-full">
          <p class="text-2xl text-center md:text-left">Game Instructions</p>
          <ul class="list-inside list-decimal">
            <li>
              Your goal is to correctly mark each of the cells
              (<i class="cell cell-unrevealed"></i>) as safe
              (<i class="cell w-full cell-empty inline-block"></i>) or flagged
              (<i class="cell cell-flag"></i>).
            </li>
            <li>Click the cell cycle through the states.</li>
            <li>
              Once you have marked all the cells, click the
              <span class="text-green-500">Submit</span> button to check your
              solution.
            </li>
            <li>
              Want to start over? Click
              <span class="text-red-500">Clear</span> to reset the board.
            </li>
            <li>
              Want to try a different puzzle? Click the
              <span class="text-blue-500">New Puzzles</span> button to get a new
              puzzle.
            </li>
          </ul>
          <div class="divider m-0"></div>
        </div>
      </template>

      <template #right>
        <div></div>
      </template>


      <template v-slot:default="props">
        {{ props.scale }}
        <MinesweeperPuzzle
          :class="[
            'bg-gray-600 rounded-md border-5 mx-auto max-w-fit',
            ms.puzzle.completed_at ? 'border-green-500' : '',
            display_unsolved ? 'border-red-500' : '']"
          :store="ms"
          :puzzle="ms.puzzle"
          :scale="props.scale"
          v-if="ms.puzzle"
          @game-event="on_game_event"
        />

        <div class="flex flex-col items-center">
          <div class="flex flex-row justify-center w-full gap-2 my-2">
            <button class="btn btn-error w-30" @click="ms.clear_state()">
              Clear
            </button>
            <button class="btn btn-success w-30" @click="check_game_solved">
              Submit
            </button>
            <button class="btn btn-info w-30" @click="on_new_puzzle">
              New Puzzles
            </button>
          </div>
          <div
            v-if="message"
            role="alert"
            class="alert alert-warning mb-2 rounded-2xl text-xl text-center w-64"
          >
            {{ message }}
          </div>
        </div>
      </template>
    </GameLayout>
  </div>
</template>
