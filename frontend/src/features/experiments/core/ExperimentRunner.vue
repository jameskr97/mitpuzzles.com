<script setup lang="ts">
import { computed, defineAsyncComponent, onMounted, type PropType } from "vue";
import { useExperiment } from "@/features/experiments/core/useExperiment";
import { useCurrentExperiment } from "@/store/useCurrentExperiment.ts";
import type { ExperimentConfig } from "./types";
import StepExperiment from "@/features/experiments/components/StepExperiment.vue";
import { useGameHistoryStore } from "@/store/useGameHistoryStore.ts";
import { useExperimentContext } from "@/features/experiments/core/useExperimentContext.ts";
import { useAppConfig } from "@/store/app.ts";

// Props
const isDev = import.meta.env.DEV;
const props = defineProps({
  config: { type: Object as PropType<ExperimentConfig>, required: true },
});

// Use both experiment systems
const experiment = useExperiment(props.config);
const experimentContext = useExperimentContext();
const historyStore = useGameHistoryStore();
const experimentStore = useCurrentExperiment();
const appStore = useAppConfig()
appStore.setMode('prolific')

// Initialize the experiment context with randomized trials
onMounted(async () => {
  const timestamp = Date.now();
  const urlParams = new URLSearchParams(window.location.search);
  experimentStore.prolific_participant_id = urlParams.get("PROLIFIC_PID") ?? `test-participant-${timestamp}`;
  experimentStore.prolific_study_id = urlParams.get("STUDY_ID") ?? `test-study-${timestamp}`;
  experimentStore.prolific_session_id = urlParams.get("SESSION_ID") ?? `test-session-${timestamp}`;

  console.log(
    `🔬 Prolific Parameters Initialized: prolific_id=${experimentStore.prolific_participant_id}, study_id=${experimentStore.prolific_study_id}, session_id=${experimentStore.prolific_session_id}`,
  );

  await historyStore.initializeStore();
  experimentContext.initializeExperiment(props.config);
});

// Use context for progress instead of original experiment
const progressPercentage = computed(() => Math.round(experimentContext.progress.value));

const stepComponents = computed(() => {
  const components: Record<string, any> = {};

  // Use randomized config from context
  const config = experimentContext.currentStep.value ? { steps: [experimentContext.currentStep.value] } : props.config;

  // Process each step one by one
  for (let i = 0; i < props.config.steps.length; i++) {
    const step = props.config.steps[i];
    const componentName = step.component;

    components[componentName] = defineAsyncComponent(async () => {
      const experimentId = experiment.context.value.experimentId;
      console.log(experimentId);
      // Try experiment-specific component first
      try {
        console.log(`Trying experiment-specific: ${componentName}`);
        return await import(`@/features/experiments/definitions/${experimentId}/${componentName}.vue`);
      } catch (error1) {
        console.log(`Experiment-specific failed, trying shared components`);

        // Try shared components
        try {
          return await import(`@/features/experiments/components/${componentName}.vue`);
        } catch (error2) {
          console.error(`Both paths failed for ${componentName}`);

          // Return error component
          return await import("../components/StepError.vue");
        }
      }
    });
  }

  return components;
});

// Current step component - use context instead of experiment
const currentStepComponent = computed(() => {
  const step = experimentContext.currentStep.value;
  return step ? stepComponents.value[step.component] : null;
});

// Handle step completion with context
function handleStepComplete(data?: any) {
  const currentStep = experimentContext.currentStep.value;
  if (!currentStep) return;

  // Store step data in context with Prolific metadata
  if (data) {
    const enrichedData = {
      ...data,
      timestamp: Date.now(),
    };
    experimentContext.storeStepData(currentStep.id, enrichedData);
  }

  // Special handling for puzzle trials
  if (currentStep.type === "puzzle-trial") {
    const trialInfo = experimentContext.getCurrentTrialInfo();

    // Store experiment event in history with Prolific context
    historyStore.addExperimentEvent(
      props.config.id || "unknown_experiment",
      currentStep.id,
      currentStep.props?.puzzleType || "unknown_puzzle",
      {
        action: "puzzle_trial_completed",
        cell: { row: 0, col: 0 },
        timestamp: Date.now(),
        trial_info: trialInfo,
        ...data,
      },
      session_id.value || undefined,
    );
  }

  // Save to original experiment system too (for compatibility)
  if (data) {
    experiment.saveStepData(data);
  }

  // Advance to next step
  experimentContext.nextStep();
  experiment.nextStep(); // Keep both in sync
}

// Handle step navigation
function handleStepBack() {
  experimentContext.previousStep();
  experiment.previousStep();
}

function handleStepSkip() {
  const currentStep = experimentContext.currentStep.value;
  if (currentStep) {
    experimentContext.storeStepData(currentStep.id, {
      skipped: true,
      timestamp: Date.now(),
    });
  }
  experimentContext.nextStep();
  experiment.skipStep();
}

// Get trial info for display
const currentTrialInfo = computed(() => {
  return experimentContext.getCurrentTrialInfo();
});

// Export data function for development
// function exportData() {
//   const contextData = experimentContext.getExperimentData();
//   const historyData = historyStore.getExperimentSummary();
//
//   console.log("Experiment Context Data:", contextData);
//   console.log("History Data:", historyData);
//
//   // Download as JSON for easy inspection
//   const combinedData = {
//     contextData,
//     historyData,
//     exportedAt: new Date().toISOString(),
//   };
//
//   const blob = new Blob([JSON.stringify(combinedData, null, 2)], { type: 'application/json' });
//   const url = URL.createObjectURL(blob);
//   const a = document.createElement('a');
//   a.href = url;
//   a.download = `experiment-data-${Date.now()}.json`;
//   a.click();
//   URL.revokeObjectURL(url);
// }
</script>

<template>
  <!--  this div -->
  <div class="">
    <!--    <Container-->
    <!--      class="fixed top-2 left-1/2 transform -translate-x-[27.7ch] max-w-[80ch] w-full mx-4 bg-white shadow p-2 z-50"-->
    <!--    >-->
    <!--      <div class="flex mt-2 items-center justify-between">-->
    <!--        <span class="text-xl">{{ progressPercentage }}%</span>-->
    <!--        <Progress :model-value="progressPercentage" />-->
    <!--      </div>-->

    <!--      &lt;!&ndash; Show trial info for puzzle steps &ndash;&gt;-->
    <!--      <div v-if="currentTrialInfo" class="text-sm text-gray-600 mt-1 text-center">-->
    <!--        Trial {{ currentTrialInfo.currentTrialNumber }} of {{ currentTrialInfo.totalTrials }}-->
    <!--        <span class="text-xs">({{ currentTrialInfo.trialId }})</span>-->
    <!--      </div>-->
    <!--    </Container>-->
    <StepExperiment
      v-if="experimentContext.currentStep.value"
      :step="experimentContext.currentStep.value"
      :component="currentStepComponent"
      :context="{
        ...experiment.context.value,
        trialInfo: currentTrialInfo,
        experimentContext: experimentContext,
      }"
      @complete="handleStepComplete"
      @back="handleStepBack"
      @skip="handleStepSkip"
    />
  </div>

  <!-- Debug panel (development only) -->
  <div v-if="isDev" class="fixed bottom-4 right-4 bg-gray-800 text-white p-3 rounded-lg text-xs max-w-xs">
    <div class="font-bold mb-1">Debug Info</div>
    <div>Session: {{ experiment.sessionId.slice(-8) }}</div>
    <div>Participant: {{ experiment.participantId }}</div>
    <div>Step: {{ experimentContext.currentStep.value?.id }}</div>
    <div>Progress: {{ experimentContext.currentStepIndex.value + 1 }}/{{ experimentContext.totalSteps }}</div>

    <!-- Prolific Parameters -->
    <div class="mt-2 border-t border-gray-600 pt-2">
      <div class="font-bold">Prolific Params</div>
      <div class="text-xs">
        <div>PID: {{ experimentStore.prolific_session_id || "Missing" }}</div>
        <div>Study: {{ experimentStore.prolific_study_id || "Missing" }}</div>
        <div>Session: {{ experimentStore.prolific_session_id || "Missing" }}</div>
      </div>
    </div>

    <div v-if="currentTrialInfo">
      Trial: {{ currentTrialInfo.currentTrialNumber }}/{{ currentTrialInfo.totalTrials }}
    </div>
    <div>Puzzle Active: {{ !!experiment.puzzleController.value }}</div>
    <div v-if="experiment.puzzleController.value">
      Trial ID: {{ experiment.puzzleController.value.trialId.value?.slice(-8) }}
    </div>

    <!-- Show trial order -->
    <!--    <details class="mt-2">-->
    <!--      <summary class="cursor-pointer">Trial Order</summary>-->
    <!--      <div class="text-xs mt-1">-->
    <!--        <div v-if="experimentContext.getExperimentData().trialOrder">-->
    <!--          <div v-for="(trial, i) in experimentContext.getExperimentData().trialOrder" :key="trial.stepId"-->
    <!--               :class="{ 'font-bold': trial.stepId === experimentContext.currentStep.value?.id }">-->
    <!--            {{ i + 1 }}: {{ trial.stepId }} ({{ trial.puzzleId }})-->
    <!--          </div>-->
    <!--        </div>-->
    <!--      </div>-->
    <!--    </details>-->
  </div>
</template>
