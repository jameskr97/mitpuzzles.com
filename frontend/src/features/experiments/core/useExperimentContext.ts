import { ref, computed } from 'vue';
import type { ExperimentConfig } from "@/features/experiments/core/types.ts";

// Simple experiment state
const currentStepIndex = ref(0);
const experimentConfig = ref<ExperimentConfig | null>(null);
const originalConfig = ref<ExperimentConfig | null>(null);
const experimentData = ref<Record<string, any>>({});
const totalPoints = ref(0);
const boardSize = ref(10);

export const useExperimentContext = () => {
  // Initialize experiment with randomized trials
  const initializeExperiment = (config: ExperimentConfig) => {
    originalConfig.value = JSON.parse(JSON.stringify(config)); // Deep copy

    // Randomize trial order
    const randomizedConfig = randomizeTrials(config);
    experimentConfig.value = randomizedConfig;

    currentStepIndex.value = 0;
    experimentData.value = {
      experimentId: config.id,
      startTime: Date.now(),
      participantId: generateParticipantId(),
      stepData: {},
      trialOrder: getTrialOrder(randomizedConfig),
      originalTrialOrder: getTrialOrder(config),
    };

    console.log('Experiment initialized:', config.id);
    console.log('Trial order:', experimentData.value.trialOrder);
  };

  // Current step
  const currentStep = computed(() => {
    if (!experimentConfig.value) return null;
    return experimentConfig.value.steps[currentStepIndex.value];
  });

  // Progress
  const totalSteps = computed(() => experimentConfig.value?.steps.length || 0);
  const progress = computed(() => {
    if (totalSteps.value === 0) return 0;
    return ((currentStepIndex.value + 1) / totalSteps.value) * 100;
  });

  // Navigation
  const nextStep = () => {
    console.log("Total Steps", totalSteps.value)
    console.log("Current Step Index", currentStepIndex.value)
    if (currentStepIndex.value < totalSteps.value - 1) {
      currentStepIndex.value++;
      console.log('Advanced to step:', currentStep.value?.id);
    }
  };

  const previousStep = () => {
    if (currentStepIndex.value > 0) {
      currentStepIndex.value--;
      console.log('Moved back to step:', currentStep.value?.id);
    }
  };

  const goToStep = (stepId: string) => {
    if (!experimentConfig.value) return;

    const stepIndex = experimentConfig.value.steps.findIndex(step => step.id === stepId);
    if (stepIndex !== -1) {
      currentStepIndex.value = stepIndex;
      console.log('Jumped to step:', stepId);
    }
  };

  // Data storage
  const storeStepData = (stepId: string, data: any) => {
    if (!experimentData.value.stepData) {
      experimentData.value.stepData = {};
    }
    experimentData.value.stepData[stepId] = {
      ...experimentData.value.stepData[stepId],
      ...data,
      timestamp: Date.now(),
    };

    console.log('Stored data for step:', stepId, data);
  };

  const getStepData = (stepId: string) => {
    return experimentData.value.stepData?.[stepId] || {};
  };

  // Check if experiment is complete
  const isComplete = computed(() => {
    return currentStepIndex.value >= totalSteps.value - 1;
  });

  // Check if current step is a trial
  const isCurrentStepTrial = computed(() => {
    return currentStep.value?.type === 'puzzle-trial';
  });

  // Get trial info
  const getCurrentTrialInfo = () => {
    if (!isCurrentStepTrial.value || !currentStep.value) return null;

    const trialOrder = experimentData.value.trialOrder || [];
    const currentTrialIndex = trialOrder.findIndex(trial => trial.stepId === currentStep.value.id);

    return {
      currentTrialNumber: currentTrialIndex + 1,
      totalTrials: trialOrder.length,
      trialId: currentStep.value.id,
      puzzleId: currentStep.value.props?.definition?.id,
    };
  };

  // Get all experiment data for export
  const getExperimentData = () => {
    return {
      ...experimentData.value,
      endTime: Date.now(),
      totalDuration: Date.now() - experimentData.value.startTime,
      completionStatus: isComplete.value ? 'completed' : 'in_progress',
    };
  };

  return {
    // State
    currentStep,
    currentStepIndex: computed(() => currentStepIndex.value),
    totalSteps,
    progress,
    isComplete,
    isCurrentStepTrial,

    // Actions
    initializeExperiment,
    nextStep,
    previousStep,
    goToStep,
    storeStepData,
    getStepData,
    getCurrentTrialInfo,
    getExperimentData,
    totalPoints,
    boardSize
  };
};

// Randomize the order of puzzle trials
function randomizeTrials(config: ExperimentConfig): ExperimentConfig {
  const newConfig = JSON.parse(JSON.stringify(config)); // Deep copy

  // Find all trial steps
  const trialSteps = newConfig.steps.filter(step => step.type === 'puzzle-trial');
  const nonTrialSteps = newConfig.steps.filter(step => step.type !== 'puzzle-trial');

  // Shuffle trials using Fisher-Yates algorithm
  const shuffledTrials = [...trialSteps];
  for (let i = shuffledTrials.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [shuffledTrials[i], shuffledTrials[j]] = [shuffledTrials[j], shuffledTrials[i]];
  }

  // Rebuild steps array maintaining non-trial step positions
  const newSteps = [];
  let trialIndex = 0;

  for (const step of newConfig.steps) {
    if (step.type === 'puzzle-trial') {
      newSteps.push(shuffledTrials[trialIndex++]);
    } else {
      newSteps.push(step);
    }
  }

  newConfig.steps = newSteps;
  return newConfig;
}

// Get trial order info
function getTrialOrder(config: ExperimentConfig) {
  return config.steps
    .filter(step => step.type === 'puzzle-trial')
    .map((step, index) => ({
      stepId: step.id,
      originalIndex: index,
      puzzleId: step.props?.definition?.id,
      puzzleType: step.props?.puzzleType,
    }));
}

// Generate a simple participant ID
function generateParticipantId(): string {
  return `participant_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}
