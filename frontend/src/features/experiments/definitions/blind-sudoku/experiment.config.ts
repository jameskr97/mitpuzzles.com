import type { ExperimentConfig } from "@/features/experiments/core/types.ts";

const config: Partial<ExperimentConfig> = {
  id: "blind-sudoku",
  title: "Blind Sudoku Study",
  description: "A pilot sudoku experiment to test the feasibility of a larger study.",

  settings: {
    allowRefresh: true,
    saveFrequency: 5000, // Save every 5 seconds
    autoAdvance: false,
  },

  steps: [
    // Step 1: Consent
    {
      id: "consent",
      type: "consent",
      component: "StepConsent",
      props: {
        content_file: "consent.md",
        requiredAgreement: true,
      },
      nextButtonText: "I Consent",
    },

    // Step 2: Instructions
    {
      id: "instructions",
      type: "instructions",
      component: "instructions",
    },

    // Step 3: Trial 1
    {
      id: "trial-1",
      type: "puzzle-trial",
      component: "game",
      props: {
        puzzleType: "sudoku",
        definition: {
          id: 10664,
          puzzle_type: "sudoku",
          rows: 9,
          cols: 9,
          initial_state: [
            [6, 3, -1, 9, 5, 4, 1, 2, 8],
            [9, -1, -1, 6, -1, 3, -1, -1, 5],
            [1, -1, -1, -1, -1, 7, 6, -1, 9],
            [8, 7, 2, 1, -1, -1, -1, -1, 4],
            [4, -1, -1, 2, 6, 5, -1, 8, -1],
            [-1, 5, -1, -1, -1, -1, -1, -1, 1],
            [2, 9, 4, 5, -1, 6, 8, 1, -1],
            [-1, -1, -1, -1, 8, 1, -1, 7, -1],
            [7, 8, -1, 3, 9, -1, -1, 5, -1],
          ],
          solution_hash: "637954128928613745145827639872139564419265387356748291294576813563481972781392456",
        },
      },
    },

    {
      id: "trial-2",
      type: "puzzle-trial",
      component: "game",
      props: {
        puzzleType: "sudoku",
        definition: {
          id: 10922,
          puzzle_type: "sudoku",
          rows: 9,
          cols: 9,
          initial_state: [
            [-1, -1, 2, 3, 7, -1, 9, -1, 6],
            [3, -1, 7, 8, -1, 9, -1, 4, 2],
            [-1, 8, -1, 2, 1, -1, -1, 5, 3],
            [5, 2, -1, -1, 9, 6, -1, -1, -1],
            [-1, 3, 4, -1, 2, 8, 6, -1, 1],
            [7, -1, 8, 4, 3, -1, -1, 2, -1],
            [-1, 1, 5, 6, 4, -1, -1, 9, 8],
            [8, -1, 3, -1, -1, 2, -1, -1, 7],
            [-1, -1, -1, 9, 8, 3, -1, 1, -1],
          ],
          solution_hash: "142375986357869142689214753521796834934528671768431529215647398893152467476983215",
        },
      },
    },

    {
      id: "trial-3",
      type: "puzzle-trial",
      component: "game",
      props: {
        puzzleType: "sudoku",
        definition: {
          id: 10849,
          puzzle_type: "sudoku",
          rows: 9,
          cols: 9,
          initial_state: [
            [1, -1, 5, 8, -1, 2, 6, 4, 9],
            [7, -1, 6, 4, 1, 9, 2, 3, -1],
            [4, -1, 2, 3, -1, -1, -1, 1, 7],
            [-1, 7, -1, 1, -1, 4, 9, 2, 6],
            [8, 4, 1, 2, 9, -1, 7, -1, -1],
            [6, 2, 9, 7, -1, -1, -1, 8, 1],
            [-1, 6, 7, 5, -1, 8, 1, -1, -1],
            [3, 1, 8, 9, 4, -1, 5, 6, 2],
            [9, 5, 4, 6, 2, -1, 3, 7, -1],
          ],
          solution_hash: "135872649786419235492365817573184926841296753629753481267538194318947562954621378",
        },
      },
    },

    // Step 6: Survey
    {
      id: "survey",
      type: "survey",
      component: "survey",
      props: {
        completion_code: "CZPLX09E",
      }
    },
  ],
};

export default config;
