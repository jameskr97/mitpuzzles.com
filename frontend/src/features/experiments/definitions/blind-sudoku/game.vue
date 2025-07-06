<script setup lang="ts">
import type { ExperimentContext } from "@/features/experiments/core/types.ts";
import Container from "@/components/ui/Container.vue";
import { Button } from "@/components/ui/button";
import PuzzleSudoku from "@/features/games/sudoku/sudoku.puzzle.vue";
import { computed, ref, watch } from "vue";
import { remap } from "@/services/util.ts";
import type { PuzzleDefinition } from "@/services/game/engines/types.ts";
import { useExperimentPuzzle } from "@/features/experiments/core/useExperimentPuzzle.ts";
import { createPuzzleInteractionBridge } from "@/features/games.composables/setupPuzzleInteractionBridge.ts";
import { withSudokuBehaviors } from "@/features/games/sudoku/useSudokuCellHighlighter.ts";
import { withSudokuFocusBehavior } from "@/features/games/sudoku/useSudokuFocusHighlighter.ts";
import { Badge } from "@/components/ui/badge";
import { withSudokuValidationBehavior } from "@/features/games/sudoku/useSudokuValidationHighlighter.ts";
import { useGameHistoryStore } from "@/store/useGameHistoryStore.ts";
import { useExperimentContext } from "@/features/experiments/core/useExperimentContext.ts";

/**
 * Render each puzzle session sent by the backend in order.
 * When the user solves one, automatically load the next.
 * After the last puzzle is solved, advance to the next experiment step.
 */
const props = defineProps({
  context: {
    type: Object as PropType<ExperimentContext>,
    required: true,
  },
  definition: {
    type: Object as PropType<PuzzleDefinition>,
    required: true,
  },
});

const experimentContext = useExperimentContext();
const historyStore = useGameHistoryStore();
const trialInfo = computed(() => experimentContext.getCurrentTrialInfo())
const pc = useExperimentPuzzle(
  props.context.currentStep.toString(), // or use step id: context.currentStep.id
  props.definition,
  experimentContext
);
const bridge = createPuzzleInteractionBridge(pc);
const b1 = withSudokuBehaviors(pc, bridge);
const b2 = withSudokuFocusBehavior(pc, bridge);
const b3 = withSudokuValidationBehavior(pc, bridge);
b2.setShouldRecordFocus("experiment");

const can_finish_puzzle = ref(false);
const is_trial_active = ref(true);
watch(() => pc.state_puzzle.value.board, (newBoard) => {
  const has_empty = pc.state_puzzle.value.board.some(row => row.some(cell => cell === 0));
  can_finish_puzzle.value = has_empty;
}, { deep: true, immediate: true });

const scale_remapped = computed(() => remap([1, 100], [1, 4], experimentContext.boardSize.value));

function onFinish() {
  b1.clearActiveCell();
  b2.setEnabled(false)
  const incorrect = pc.get_incorrect_cells()
  const correct = pc.get_correct_cells()
  b3.setMultipleIncorrect(incorrect)
  b3.setMultipleCorrect(correct)
  is_trial_active.value = false;

  const total_points = (correct.length  * 3) - (incorrect.length * 3);
  experimentContext.totalPoints.value += total_points;
  experimentContext.totalPoints.value = Math.max(0, experimentContext.totalPoints.value);
}

function onNextTrial() {
  experimentContext.nextStep()
}

</script>

<template>
  <div class="mx-auto p-2 flex-col w-full mt-9">
    <div class="flex flex-col items-center w-full mx-auto justify-around gap-2 px-2">
      <div class="flex flex-col w-full gap-4">
        <!-- Control Bar -->
        <Container class="w-full md:max-w-prose mt-2 md:mt-0 mx-auto">
          <div class="flex flex-col">
            <div class="flex flex-row w-full">
              <v-icon name="co-magnifying-glass" :scale="1.5" />
              <input type="range" min="1" max="100" step="1" v-model="experimentContext.boardSize.value" class="mx-2 w-full" />
              <!--              <Slider v-model="scale" :min="1" :max="100" :step="1" class="mx-2" />-->
            </div>

            <!-- Buttons -->
            <div class="grid grid-cols-1 w-full gap-1 mt-2">
              <Button v-if="is_trial_active" :disabled="can_finish_puzzle" variant="blue" class="w-full" @click="onFinish"> Finish Trial </Button>
              <Button v-else variant="blue" class="w-full" @click="onNextTrial">Next Trial</Button>
            </div>
          </div>
        </Container>
        <!-- Point Counter -->
        <Container ref="pointBox" class="flex flex-col items-center text-4xl text-center max-w-prose mx-auto">
          <Badge variant="outline">Points</Badge>
          {{experimentContext.totalPoints.value}}
        </Container>
      </div>
      <div class="grow">
        <div class="flex flex-col items-center">
          <div
            ref="board"
            class="p-2 flex flex-col mt-4 border rounded shadow"
            :class="{ 'pointer-events-none': false }"
          >
            <PuzzleSudoku :state="pc.state_puzzle.value" :scale="scale_remapped" :interact="bridge" />
          </div>
        </div>
      </div>

      <Container class="max-w-prose mx-auto mt-4">
        <p>
          Click on any square to <span class="font-bold">reveal</span> it, and it's corresponding part of the board.
        </p>
        <p>
          Press keys 1 to 9 to <span class="font-bold">enter a number</span> into the selected cell
          <span class="inline-block h-5 w-5 bg-blue-500 rounded"></span>.
        </p>
      </Container>
    </div>
  </div>
</template>
