// frontend/src/features/experiments/core/types.ts

import type { PuzzleController, PuzzleDefinition } from "@/services/game/engines/types";
import type { PUZZLE_TYPES } from "@/constants";

export interface ExperimentConfig {
  id: string;
  title: string;
  description: string;
  version: string;
  steps: ExperimentStep[];
  settings: ExperimentSettings;
}

export interface ExperimentStep {
  id: string;
  type: "consent" | "instructions" | "puzzle-trial" | "survey" | "break" | "custom";
  nextButtonText?: string; // for navigation
  component: string; // Vue component name or path
  props?: Record<string, any>;
}

export interface ExperimentSettings {
  allowRefresh: boolean;
  saveFrequency: number; // milliseconds
  autoAdvance?: boolean;
}


export interface ExperimentContext {
  experimentId: string;
  participantId: string;
  sessionId: string;
  currentStep: number;
  totalSteps: number;
  stepData: Record<string, any>;
  experimentData: ExperimentData;
  puzzleController?: PuzzleController;

  // Navigation methods
  nextStep: () => void;
  previousStep: () => void;
  skipStep: () => void;
  jumpToStep: (stepId: string) => void;

  // Data methods
  saveStepData: (data: any) => Promise<void>;
  getStepData: (stepId?: string) => any;

  // Puzzle methods (when in puzzle step)
  triggerInterruption: (interruptionId: string) => void;
  pausePuzzle: () => void;
  resumePuzzle: () => void;

  // Utility methods
  getParticipantAssignment: () => string;
  isLastStep: () => boolean;
  getTimeElapsed: () => number;
}

export interface ExperimentData {
  participantId: string;
  sessionId: string;
  experimentId: string;
  startTime: number;
  endTime?: number;
  abTestAssignment?: string;
  steps: StepData[];
  puzzleTrials: PuzzleTrialData[];
  interruptions: InterruptionData[];
  metadata: ExperimentMetadata;
}

export interface StepData {
  stepId: string;
  stepType: string;
  startTime: number;
  endTime?: number;
  data: any; // step-specific data
  skipped: boolean;
}

export interface PuzzleTrialData {
  trialId: string;
  puzzleType: PUZZLE_TYPES;
  puzzleDefinition: any;
  startTime: number;
  endTime?: number;
  completed: boolean;
  moves: PuzzleMoveData[];
  interruptions: string[]; // interruption ids that occurred
  finalState: any;
  metadata: any;
}

export interface PuzzleMoveData {
  timestamp: number;
  moveType: string;
  position: { row: number; col: number; zone?: string };
  oldValue: any;
  newValue: any;
  gameState?: any; // optional snapshot
}

export interface InterruptionData {
  interruptionId: string;
  trialId: string;
  triggerTime: number;
  triggerCondition: any;
  responseTime?: number;
  response: any;
  gameStateAtTrigger: any;
}

export interface ExperimentMetadata {
  userAgent: string;
  screenSize: { width: number; height: number };
  timezone: string;
  language: string;
  experimentVersion: string;
  frameworkVersion: string;
}

// Vue component prop types for step components
export interface BaseStepProps {
  context: ExperimentContext;
}

export interface ConsentStepProps extends BaseStepProps {
  content: string; // markdown content
  requiredAgreement: boolean;
}

export interface InstructionsStepProps extends BaseStepProps {
  content: string; // markdown content
  media?: { type: "image" | "video"; src: string }[];
  allowSkip: boolean;
}

export interface SurveyStepProps extends BaseStepProps {
  questions: SurveyQuestion[];
  submitText?: string;
  requiredQuestions?: string[];
}

export interface SurveyQuestion {
  id: string;
  type: "text" | "textarea" | "select" | "multiselect" | "radio" | "checkbox" | "scale" | "number";
  question: string;
  options?: string[] | { value: string; label: string }[];
  required?: boolean;
  validation?: {
    min?: number;
    max?: number;
    pattern?: string;
  };
}

export interface PuzzleTrialStepProps extends BaseStepProps {
  puzzleType: PUZZLE_TYPES;
  def: PuzzleDefinition,
}

export interface BreakStepProps extends BaseStepProps {
  duration: number; // seconds
  message: string;
  allowSkip: boolean;
}

// Event system for experiment flow
export interface ExperimentEvent {
  type: string;
  timestamp: number;
  data: any;
}
