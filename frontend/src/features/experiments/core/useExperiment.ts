// frontend/src/features/experiments/core/useExperiment.ts

import { computed, provide, reactive, ref } from "vue";
import { useExperimentData } from "./useExperimentData";
import { useExperimentPuzzle } from "./useExperimentPuzzle";
import type { ExperimentConfig, ExperimentContext, ExperimentData, StepData } from "./types";
import type { PUZZLE_TYPES } from "@/constants";

// Generate unique session ID
function generateSessionId(): string {
  return `exp_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

// Generate participant ID (could be from URL params or generated)
function generateParticipantId(): string {
  // Check URL params first
  const urlParams = new URLSearchParams(window.location.search);
  const prolificId = urlParams.get("PROLIFIC_PID");
  const studyId = urlParams.get("STUDY_ID");
  const sessionId = urlParams.get("SESSION_ID");

  if (prolificId) {
    return `prolific_${prolificId}`;
  }

  // Generate random ID
  return `participant_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`;
}

export function useExperiment(config: ExperimentConfig) {
  // Core state
  const sessionId = generateSessionId();
  const participantId = generateParticipantId();
  const currentStepIndex = ref(0);
  const isInitialized = ref(false);
  const isCompleted = ref(false);
  const stepHistory = ref<string[]>([]);

  // Step data tracking
  const stepData = reactive<Record<string, any>>({});
  const currentStepStartTime = ref(0);

  // A/B testing
  const abTestAssignment = ref<string>();

  // Data management
  const dataManager = useExperimentData(sessionId);

  // Puzzle controller (only when in puzzle step)
  const puzzleController = ref<any>(null);

  // Interruption handling
  const activeInterruption = ref<any>(null);
  const interruptionResolver = ref<((response: any) => void) | null>(null);

  // Computed properties
  const currentStep = computed(() => config.steps[currentStepIndex.value] || null);
  const totalSteps = computed(() => config.steps.length);
  const isLastStep = computed(() => currentStepIndex.value >= totalSteps.value - 1);
  const experimentProgress = computed(() => (currentStepIndex.value + 1) / totalSteps.value);

  // Initialize experiment
  async function initializeExperiment(): Promise<void> {
    if (isInitialized.value) return;

    try {
      // Initialize data manager
      const experimentData = await dataManager.initializeExperiment(config.id, participantId);

      // Start periodic data saves
      // dataManager.startPeriodicSave(config.settings.saveFrequency);

      // Check for recovery from page refresh
      await attemptRecovery(experimentData);

      isInitialized.value = true;
      console.log(`Experiment initialized: ${config.id}, session: ${sessionId}`);
    } catch (error) {
      console.error("Failed to initialize experiment:", error);
      throw error;
    }
  }

  // Attempt to recover from page refresh
  async function attemptRecovery(experimentData: ExperimentData): Promise<void> {
    if (experimentData.steps.length > 0) {
      // Find the last incomplete step
      const lastCompleteStepIndex =
        experimentData.steps
          .map((step, index) => ({ step, index }))
          .filter(({ step }) => step.endTime)
          .pop()?.index ?? -1;

      currentStepIndex.value = Math.min(lastCompleteStepIndex + 1, config.steps.length - 1);

      // Restore step data
      experimentData.steps.forEach((stepDataItem) => {
        stepData[stepDataItem.stepId] = stepDataItem.data;
      });

      console.log(`Recovered experiment at step ${currentStepIndex.value}`);
    }
  }

  // Navigation methods
  async function nextStep(): Promise<void> {
    if (isLastStep.value) {
      await completeExperiment();
      return;
    }

    await recordStepCompletion();
    currentStepIndex.value++;
    await startNewStep();
  }

  async function previousStep(): Promise<void> {
    if (currentStepIndex.value > 0) {
      await recordStepCompletion();
      currentStepIndex.value--;
      await startNewStep();
    }
  }

  async function skipStep(): Promise<void> {
    await recordStepCompletion(true);
    currentStepIndex.value++;
    await startNewStep();
  }

  async function jumpToStep(stepId: string): Promise<void> {
    const targetIndex = config.steps.findIndex((s) => s.id === stepId);
    if (targetIndex >= 0) {
      await recordStepCompletion();
      currentStepIndex.value = targetIndex;
      await startNewStep();
    }
  }

  // Step management
  async function startNewStep(): Promise<void> {
    const step = currentStep.value;
    if (!step) return;

    currentStepStartTime.value = Date.now();
    stepHistory.value.push(step.id);

    // Initialize puzzle controller if this is a puzzle step
    if (step.type === "puzzle-trial") {
      const puzzleType = step.props?.puzzleType as PUZZLE_TYPES;
      if (puzzleType) {
        puzzleController.value = await useExperimentPuzzle(puzzleType, sessionId, createContext());
      }
    } else {
      puzzleController.value = null;
    }

    console.log(`Started step: ${step.id} (${step.type})`);
  }

  async function recordStepCompletion(skipped: boolean = false): Promise<void> {
    const step = currentStep.value;
    if (!step) return;

    const stepDataItem: StepData = {
      stepId: step.id,
      stepType: step.type,
      startTime: currentStepStartTime.value,
      endTime: Date.now(),
      data: stepData[step.id] || {},
      skipped,
    };

    dataManager.recordStepCompletion(stepDataItem);

    // Clean up puzzle controller if needed
    if (puzzleController.value?.cleanup) {
      puzzleController.value.cleanup();
      puzzleController.value = null;
    }
  }

  // Data methods
  async function saveStepData(data: any): Promise<void> {
    const step = currentStep.value;
    if (!step) return;

    stepData[step.id] = { ...stepData[step.id], ...data };
    await dataManager.saveExperimentData();
  }

  function getStepData(stepId?: string): any {
    const targetStepId = stepId || currentStep.value?.id;
    return targetStepId ? stepData[targetStepId] : null;
  }

  // Interruption handling
  async function triggerInterruption(interruptionId: string): Promise<any> {
    if (!puzzleController.value) return;

    const interruption = puzzleController.value.interruptions.value.find((i: any) => i.id === interruptionId);

    if (!interruption) return;

    activeInterruption.value = interruption;

    return new Promise((resolve) => {
      interruptionResolver.value = resolve;
      // The interruption component will call resolveInterruption when done
    });
  }

  function resolveInterruption(response: any): void {
    if (interruptionResolver.value) {
      interruptionResolver.value(response);
      interruptionResolver.value = null;
    }
    activeInterruption.value = null;
  }

  // Puzzle-specific methods
  function pausePuzzle(): void {
    if (puzzleController.value?.pauseForInterruption) {
      puzzleController.value.pauseForInterruption();
    }
  }

  function resumePuzzle(): void {
    if (puzzleController.value?.resumeFromInterruption) {
      puzzleController.value.resumeFromInterruption();
    }
  }

  // Utility methods
  function getParticipantAssignment(): string {
    return abTestAssignment.value || "default";
  }

  function getTimeElapsed(): number {
    const experimentData = dataManager.experimentData.value;
    return experimentData ? Date.now() - experimentData.startTime : 0;
  }

  // Complete experiment
  async function completeExperiment(): Promise<void> {
    await recordStepCompletion();

    const exportData = await dataManager.completeExperiment();
    isCompleted.value = true;

    dataManager.stopPeriodicSave();

    console.log("Experiment completed");
    console.log("Export data available:", exportData);

    // TODO: Submit data to server here
    // await submitDataToServer(exportData);
  }

  // Create context object for step components
  function createContext(): ExperimentContext {
    return {
      experimentId: config.id,
      participantId,
      sessionId,
      currentStep: currentStepIndex.value,
      totalSteps: totalSteps.value,
      stepData,
      experimentData: dataManager.experimentData.value!,
      puzzleController: puzzleController.value,

      // Navigation methods
      nextStep,
      previousStep,
      skipStep,
      jumpToStep,

      // Data methods
      saveStepData,
      getStepData,

      // Puzzle methods
      triggerInterruption,
      pausePuzzle,
      resumePuzzle,

      // Utility methods
      getParticipantAssignment,
      isLastStep: () => isLastStep.value,
      getTimeElapsed,
    };
  }

  // Provide context to child components
  const context = computed(() => createContext());
  provide("experimentContext", context);

  // Auto-initialize when used
  initializeExperiment();

  return {
    // State
    sessionId,
    participantId,
    currentStepIndex,
    currentStep,
    totalSteps,
    isInitialized,
    isCompleted,
    experimentProgress,
    abTestAssignment,
    activeInterruption,
    puzzleController,

    // Methods
    initializeExperiment,
    nextStep,
    previousStep,
    skipStep,
    jumpToStep,
    saveStepData,
    getStepData,
    triggerInterruption,
    resolveInterruption,
    completeExperiment,

    // Context for child components
    context,
  };
}
