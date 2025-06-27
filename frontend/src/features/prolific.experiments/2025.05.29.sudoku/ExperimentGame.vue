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

/* ------------------------------------------------------------------ */
/*  props & aliases                                                   */
/* ------------------------------------------------------------------ */
const props = defineProps({
  context: {
    type: Object as PropType<ReturnType<typeof useExperimentController>>,
    required: true,
  },
});
const ec = props.context; // experiment controller
const ws = useGameService() as WebsocketGameService;

/* ------------------------------------------------------------------ */
/*  reactive state                                                    */
/* ------------------------------------------------------------------ */
// const total_points = ref<number>(0);
// const trial_running = ref<boolean>(true);
const scale = ref<number>(1);
const scale_remapped = computed(() => remap([1, 100], [1, 4], scale.value));
// const btn_finish_trial_enabled = ref<boolean>();
// const showing_board_end = ref<boolean>(false);
// const board_interactable = ref<boolean>(true); // can the user interact with the board?

const pc = usePuzzleController("sudoku", { autoResume: false });
const bridge = createPuzzleInteractionBridge("sudoku");
withSudokuBehaviors(pc, bridge);
const b2 = withSudokuFocusBehavior(pc, bridge);
const setBehavioursEnabled = (enabled: boolean) => {
  b2.setEnabled(enabled);
};

// function finished_trial() {
//   setBehavioursEnabled(false);
//   ec.points.value += pc.state.value.points_earned!;
//   ec.finishTrial()
//   trial_running.value = false;
//   board_interactable.value = false;
//   showing_board_end.value = true;
//   // ec.setTutorialEnabled("sudoku", true);
// }

// function run_next_trial() {
//   ec.nextTrial()
//   trial_running.value = true;
//   board_interactable.value = true
//   showing_board_end.value      = false;  // hide transition overlay
//   btn_finish_trial_enabled.value = false; // gate Finish btn until board filled
//   setBehavioursEnabled(true);
//   // ec.setTutorialEnabled("sudoku", false);
// }

// disable the "Finish Trial" button until every board cell is filled
// watch(
//   () => pc.state.value,
//   (state) => {
//     if (!state) return;
//
//     // check if the board is solved
//     const is_filled = state.board.every((cell) => cell !== 0);
//     btn_finish_trial_enabled.value = is_filled;
//   },
//   { immediate: true },
// );

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

// watch(
//   () => ec.showErrorsScreen.value,
//   (show) => {
//     console.log("showErrorsScreen changed:", show);
//     setBehavioursEnabled(!show);
//   },
//   { immediate: true },
// );

function onFinish() {
  ec.finishTrial(pc.state.value.points_earned ?? 0);
}

function onNext() {
  ec.nextTrial();
}

// keep UI in sync with server‑side completion state
// watch(
//   () => ec.isCurrentCompleted,
//   (completed) => {
//     console.log("Completion state changed:", completed.value);
//     trial_running.value      = !completed.value;
//     board_interactable.value = !completed.value;
//     // ec.setTutorialEnabled("sudoku", completed.value);
//     setBehavioursEnabled(!completed.value);
//   },
//   { immediate: true },
// );
// watch(
//   () => ec.isCurrentCompleted.value,      // boolean
//   (completed) => {
//     trial_running.value      = !completed;      // swap buttons
//     board_interactable.value = !completed;      // freeze board
//     btn_finish_trial_enabled.value = completed; // enable “Next” right away
//     // ec.setTutorialEnabled("sudoku", completed); // show mistakes only in transition
//     setBehavioursEnabled(!completed);           // disable cell behaviours when frozen
//   },
//   { immediate: true },
// );
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
              <Slider :min="1" :max="100" :step="1" class="mx-2" />
            </div>

            <!-- Buttons -->
            <div class="grid grid-cols-1 w-full gap-1 mt-2">
              <Button
                variant="success"
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
