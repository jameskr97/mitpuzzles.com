// experiment.flow.ts
import Consent from '@/features/prolific.components/Consent.vue'
import ExperimentInstructions from "@/features/prolific.experiments/2025.05.29.sudoku/ExperimentInstructions.vue";
import ExperimentGame from "@/features/prolific.experiments/2025.05.29.sudoku/ExperimentGame.vue";
import ExperimentStepSurvey from '@/features/prolific.components/ExperimentStepSurvey.vue'

import mdConsent from "@/features/prolific.experiments/2025.05.29.sudoku/consent.md?raw";

export function define_2020_06_SudokuExperimentFlow() {
  return [
    { id: 'consent',      label: "Consent", component: Consent, props: { markdown: mdConsent } },
    { id: 'instructions', label: "Instructions", component: ExperimentInstructions },
    { id: 'experiment',   label: "Experiment", component: ExperimentGame },
    { id: 'survey',       label: "Survey", component: ExperimentStepSurvey },
  ];
}
