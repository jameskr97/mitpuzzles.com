<script setup lang="ts">
/**
 * Render each puzzle session sent by the backend in order.
 * When the user solves one, automatically load the next.
 * After the last puzzle is solved, advance to the next experiment step.
 */
import { computed, type PropType, ref, watch } from "vue";
import { useGameService } from "@/services/game/useGameService.ts";
import type { WebsocketGameService } from "@/services/game/WebsocketGameService.ts";
import { usePuzzleController } from "@/composables/usePuzzleController.ts";
import { createPuzzleInteractionBridge } from "@/features/games.composables/setupPuzzleInteractionBridge.ts";
import { withSudokuBehaviors } from "@/features/games/sudoku/useSudokuCellHighlighter.ts";
import PuzzleSudoku from "@/features/games/sudoku/sudoku.puzzle.vue";
import { withSudokuFocusBehavior } from "@/features/games/sudoku/useSudokuFocusHighlighter.ts";
import { Button } from "@/components/ui/button";
import Container from "@/components/ui/Container.vue";
import { Slider } from "@/components/ui/slider";
import { remap } from "@/services/util.ts";
import { Badge } from "@/components/ui/badge";
import type { useExperimentController } from "@/features/prolific.composables/useExperimentController.ts";

const props = defineProps({
  context: {
    type: Object as PropType<ReturnType<typeof useExperimentController>>,
    required: true,
  },
});
const ec = props.context; // experiment controller
const ws = useGameService() as WebsocketGameService;


const scale = ref<number>(1);
const scale_remapped = computed(() => remap([1, 100], [1, 4], scale.value));

const pc = usePuzzleController("sudoku", { autoResume: false });
const bridge = createPuzzleInteractionBridge("sudoku");
const b1 = withSudokuBehaviors(pc, bridge);
const b2 = withSudokuFocusBehavior(pc, bridge);
const setBehavioursEnabled = (enabled: boolean) => {
  b2.setEnabled(enabled);
};

watch(
  () => pc.state.value,
  (s) => s && ec.updateCanFinish(s),
);
watch(
  () => ec.showErrorsScreen.value,
  (show) => {
    console.log("showErrorsScreen changed:", show);
    setBehavioursEnabled(!show);
  },
  { immediate: true },
);
watch(
  () => ec.curBoard.value, // ← was ec.curId.value
  (board) => {
    if (!board) return;
    ws.resume("sudoku", board.session_id);

    // keep tutorial OFF only while the player is actively solving
    if (!board.is_finished) {
      ws.setTutorialEnabled(board.session_id, "sudoku", false);
    }
  },
  { immediate: true },
);



function onFinish() {
  ec.finishTrial(pc.state.value.points_earned ?? 0);
  b1.setShowCorrectCells(true);
  b1.clearActiveCell()
}

function onNext() {
  ec.nextTrial();
  b1.setShowCorrectCells(false);
}

</script>

<template>
  <div class="mx-auto p-2 flex-col w-full">
    <div class="flex flex-col items-center w-full mx-auto justify-around gap-2 px-2">
      <div class="flex flex-col w-full gap-4">
        <!-- Control Bar -->
        <Container class="w-full md:max-w-prose mt-2 md:mt-0 mx-auto">
          <div class="flex flex-col">
            <div class="flex flex-row w-full">
              <v-icon name="co-magnifying-glass" :scale="1.5" />
              <Slider v-model="scale" :min="1" :max="100" :step="1" class="mx-2" />
            </div>

            <!-- Buttons -->
            <div class="grid grid-cols-1 w-full gap-1 mt-2">
              <Button
                variant="blue"
                class="w-full"
                v-if="ec.trialRunning.value"
                :disabled="!ec.canFinishTrial.value"
                @click="onFinish"
                >Finish Trial
              </Button>
              <Button variant="blue" class="w-full" v-else @click="onNext">Next Trial</Button>
            </div>
          </div>
        </Container>
        <!-- Point Counter -->
        <Container ref="pointBox" class="flex flex-col items-center text-4xl text-center max-w-prose mx-auto">
          <Badge variant="outline">Points</Badge>
          {{ ec.points }}
        </Container>
      </div>
      <div class="grow">
        <div class="flex flex-col items-center">
          <div
            ref="board"
            class="p-2 flex flex-col mt-4 border rounded shadow"
            :class="{ 'pointer-events-none': !ec.boardInteractable.value }"
          >
            <PuzzleSudoku :state="pc.state.value" :scale="scale_remapped" :interact="bridge" />
          </div>
        </div>
      </div>

      <Container class="max-w-prose mx-auto mt-4">
        <p>Click on any square to <span class="font-bold">reveal</span> it, and it's corresponding part of the board.</p>
        <p>Press keys 1 to 9 to <span class="font-bold">enter a number</span> into the selected cell <span class="inline-block h-5 w-5 bg-blue-500 rounded "></span>.</p>
      </Container>
    </div>
  </div>
</template>
