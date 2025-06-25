<script setup lang="ts">
import { createPuzzleInteractionBridge } from "@/features/games.composables/setupPuzzleInteractionBridge.ts";
import KakurasuPuzzle from "@/features/games/kakurasu/kakurasu.puzzle.vue";
import { ref, computed, inject } from "vue";
import { remap } from "@/services/util.ts";
import type { PuzzleStateKakurasu } from "@/services/states.ts";
import { ModuleManager } from "@/services/eventbus.ts";
import type { GameModuleInterface } from "@/services/eventbus.modules/game.ts";
import { createPuzzleSession } from "@/composables/useCurrentPuzzle.ts";
import { useActivePuzzleStore } from "@/store/useActivePuzzleStore.ts";
////////////////////////////////////////////////////////////////////////
//// puzzle api data
const event_modules = inject<ModuleManager>("event_modules");
const game_module = event_modules?.getComposable?.<GameModuleInterface>("game");
const puzzle = await createPuzzleSession(game_module!, "kakurasu");
const builder = createPuzzleInteractionBridge(puzzle);
const active_puzzle_store = useActivePuzzleStore();

////////////////////////////////////////////////////////////////////////
//// ui refs
const scale = ref(50);
const scale_computed = computed(() => remap([0, 100], [1, 6], scale.value));
// const state = ref<PuzzleStateKakurasu>({
//   rows: 7,
//   cols: 7,
//   board: new Array(7 * 7).fill(KakurasuCellStates.Empty),
//   row_sum: [1, 1, 1, 4, 4, 4, 1],
//   col_sum: [2, 2, 2, 5, 5, 5, 3],
//   session_id: "my-session-id",
//   puzzle_type: "kakurasu",
// });
</script>

<template>
  <div class="text-2xl text-center w-full">Test WebSockets</div>
  <div class="divider my-0"></div>
  <div class="grid grid-cols-[2fr_1fr] gap-2 items-start justify-center">
    <div class="flex flex-col order-1 gap-2 w-full">
      <div class="border border-slate-400 flex flex-col p-2 gap-2 rounded shadow-md w-full">
        <input v-model="scale" type="range" min="0" max="100" class="range w-full user-select-none" />
        <div class="flex flex-row mb-2 gap-2 items-center">
          <button class="btn btn-primary" @click="puzzle.session.cmd_puzzle_create('7x7', 'easy')">
            Create Puzzle
          </button>
        </div>
        <p>Puzzle Session ID: {{ puzzle.session_id.value }}</p>
        <p>Puzzle Ready: {{ puzzle.is_ready.value }}</p>
        <p>Game State: {{ puzzle.state }}</p>
      </div>

      <div class="border border-slate-400 flex flex-col justify-center p-2 rounded shadow-md w-full">
        <p class="text-xl underline">All Puzzle Data</p>
        <div>
          <pre><code>{{ JSON.stringify(active_puzzle_store.puzzle_states, (k, v) => k === 'board' ? v.reduce((p: number, a: number) => p + a, 0) : v, 2) }}</code></pre>
        </div>
      </div>
    </div>

    <KakurasuPuzzle :scale="scale_computed" :state="puzzle.state.value as PuzzleStateKakurasu" :interact="builder" />
  </div>
</template>
