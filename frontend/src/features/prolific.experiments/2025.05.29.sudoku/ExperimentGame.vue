<script setup lang="ts">
import ExperimentGameView from "@/features/prolific.components/ExperimentGameView.vue";
import { computed, inject, ref } from "vue";
import { createPuzzleSession } from "@/composables/useCurrentPuzzle.ts";
import { createPuzzleInteractionBridge } from "@/features/games.composables/setupPuzzleInteractionBridge.ts";
import { ModuleManager } from "@/services/eventbus.ts";
import { gameModule, type GameModuleInterface } from "@/services/eventbus.modules/game.ts";
import { type SudokuSession, withSudokuBehaviors } from "@/features/games/sudoku/useSudokuCellHighlighter.ts";
import { withSudokuFocusBehavior } from "@/features/games/sudoku/useSudokuFocusHighlighter.ts";
import PuzzleSudoku from "@/features/games/sudoku/sudoku.puzzle.vue";
import type { PuzzleStateSudoku } from "@/services/states.ts";

// const sudoku = await usePuzzleState("sudoku");
// const interactionBridge = createPuzzleInteractionBridge(sudoku);
// const renderBehaviors = interactionBridge.getRenderBehaviors();
const scale = ref(5);

// Experiment state
const currentBoardIndex = ref(0);
const currentBoard = computed(() => props.stimlui[currentBoardIndex.value]);

// Experiment Interaction
const event_modules = inject<ModuleManager>("event_modules");
const game_module = event_modules?.getComposable?.<GameModuleInterface>("prolific");
const session = (await createPuzzleSession(game_module!, "sudoku")) as SudokuSession;
const bridge = createPuzzleInteractionBridge(session);
withSudokuBehaviors(session, bridge);
withSudokuFocusBehavior(session, bridge);

const props = defineProps({
  stimlui: { type: Array, required: true },
});
</script>

<template>
  <ExperimentGameView @scale-change="(change) => (scale = change)" @game-submitted="session.cmd_puzzle_submit">
    <div class="flex flex-col items-center">
      <div class="p-2 flex flex-col mt-4 border rounded shadow">
        <PuzzleSudoku :state="session.state.value" :scale="scale" :interact="bridge" />
      </div>
    </div>
  </ExperimentGameView>
</template>
