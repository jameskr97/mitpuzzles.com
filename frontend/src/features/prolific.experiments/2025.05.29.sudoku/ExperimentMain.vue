<script setup lang="ts">
import ExperimentView from "@/features/prolific.components/ExperimentView.vue";
import { useExperimentFlow } from "@/features/prolific.composables/useExperimentFlow.ts";
import ProgressTimeline from "@/features/prolific.components/ProgressTimeline.vue";
import ExperimentGame from "@/features/prolific.experiments/2025.05.29.sudoku/ExperimentGame.vue";
import ExperimentInstructions from "@/features/prolific.experiments/2025.05.29.sudoku/ExperimentInstructions.vue";
// markdown files
import mdConsent from "@/features/prolific.experiments/2025.05.29.sudoku/consent.md?raw";
import StepConsent from "@/features/prolific.components/StepConsent.vue";
import { useCurrentExperiment } from "@/store/useCurrentExperiment.ts";
import { on, type ProlificAuthSuccess } from "@/services/eventbus.ts";
import { ref } from "vue";
import StepSurvey from "@/features/prolific.components/StepSurvey.vue";

const stimlui = [
  {
    rows: 9,
    cols: 9,
    board: [
      0, 2, 0, 9, 3, 5, 0, 7, 8, 9, 0, 3, 7, 0, 8, 2, 0, 4, 1, 8, 7, 0, 6, 4, 9, 5, 0, 4, 6, 0, 0, 0, 0, 5, 9, 0, 7, 9,
      5, 6, 4, 1, 8, 3, 2, 2, 3, 0, 0, 8, 0, 0, 0, 7, 0, 4, 0, 1, 0, 3, 0, 0, 0, 3, 7, 2, 8, 5, 6, 4, 0, 9, 0, 1, 9, 4,
      2, 7, 3, 0, 6,
    ],
    board_initial: [
      0, 2, 0, 9, 3, 5, 0, 7, 8, 9, 0, 3, 7, 0, 8, 2, 0, 4, 1, 8, 7, 0, 6, 4, 9, 5, 0, 4, 6, 0, 0, 0, 0, 5, 9, 0, 7, 9,
      5, 6, 4, 1, 8, 3, 2, 2, 3, 0, 0, 8, 0, 0, 0, 7, 0, 4, 0, 1, 0, 3, 0, 0, 0, 3, 7, 2, 8, 5, 6, 4, 0, 9, 0, 1, 9, 4,
      2, 7, 3, 0, 6,
    ],
  },
  {
    rows: 9,
    cols: 9,
    board: [
      2, 4, 5, 0, 0, 6, 0, 0, 0, 6, 7, 0, 0, 9, 8, 0, 0, 0, 9, 8, 1, 5, 0, 7, 6, 2, 0, 0, 5, 0, 4, 6, 0, 3, 0, 0, 0, 0,
      0, 0, 0, 9, 0, 8, 4, 0, 0, 0, 3, 0, 1, 7, 5, 6, 0, 9, 7, 0, 2, 3, 0, 4, 0, 1, 0, 4, 8, 0, 0, 0, 0, 0, 0, 0, 0, 0,
      9, 1, 0, 5, 3, 7,
    ],
    board_initial: [
      2, 4, 5, 0, 0, 6, 0, 0, 0, 6, 7, 0, 0, 9, 8, 0, 0, 0, 9, 8, 1, 5, 0, 7, 6, 2, 0, 0, 5, 0, 4, 6, 0, 3, 0, 0, 0, 0,
      0, 0, 0, 9, 0, 8, 4, 0, 0, 0, 3, 0, 1, 7, 5, 6, 0, 9, 7, 0, 2, 3, 0, 4, 0, 1, 0, 4, 8, 0, 0, 0, 0, 0, 0, 0, 0, 0,
      9, 1, 0, 5, 3, 7,
    ],
  },
  {
    rows: 9,
    cols: 9,
    board: [
      4, 0, 7, 5, 0, 1, 0, 0, 0, 0, 6, 8, 0, 0, 0, 9, 1, 5, 1, 9, 5, 0, 8, 0, 7, 4, 0, 0, 0, 0, 9, 5, 0, 0, 8, 0, 9, 0,
      6, 8, 1, 4, 2, 0, 0, 5, 8, 4, 2, 6, 0, 0, 9, 0, 0, 4, 9, 0, 2, 5, 1, 0, 8, 0, 5, 0, 0, 0, 0, 0, 0, 6, 7, 1, 3, 0,
      0, 8, 0, 0, 9,
    ],
    board_initial: [
      4, 0, 7, 5, 0, 1, 0, 0, 0, 0, 6, 8, 0, 0, 0, 9, 1, 5, 1, 9, 5, 0, 8, 0, 7, 4, 0, 0, 0, 0, 9, 5, 0, 0, 8, 0, 9, 0,
      6, 8, 1, 4, 2, 0, 0, 5, 8, 4, 2, 6, 0, 0, 9, 0, 0, 4, 9, 0, 2, 5, 1, 0, 8, 0, 5, 0, 0, 0, 0, 0, 0, 6, 7, 1, 3, 0,
      0, 8, 0, 0, 9,
    ],
  },
];

const is_completed = ref(false);
const visible = ref(false);
const experiment = useCurrentExperiment();
const context = useExperimentFlow();
context.addStep("Consent", StepConsent, { markdown: mdConsent });
context.addStep("Instructions", ExperimentInstructions);
context.addStep("Experiment", ExperimentGame, { stimlui });
context.addStep("Debrief", StepSurvey);

on("auth:prolific:success", (payload: ProlificAuthSuccess) => {
  if (payload.completed) {
    is_completed.value = true;
    return;
  }
  experiment.setExperimentSession(payload.prolific_session_id, payload.current_step);
  context.goToStep(payload.current_step);
  visible.value = true;
});
</script>

<template>
  <div v-if="is_completed">
    <div class="w-full flex-1 flex flex-col items-center justify-center h-screen">
      <div class="mx-auto text-2xl max-w-100 text-center">
        This experiment has already been completed. Thank you for your participation!
      </div>
    </div>
  </div>
  <ExperimentView v-else v-show="visible" :context="context">
    <template #timeline>
      <ProgressTimeline :context="context" />
    </template>
  </ExperimentView>
</template>
