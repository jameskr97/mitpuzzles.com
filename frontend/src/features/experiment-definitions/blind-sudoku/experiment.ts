import { type experiment_definition, node_type } from "@/features/experiment-core";
import type { trial_meta } from "@/features/experiment-core/graph/types.ts";

export default {
  id: "blind-sudoku",
  title: "Blind Sudoku",
  description: "Standard Sudoku Game with blurred cells until they're selected for focus.",
  entry_node: "consent",
  nodes: [
    {
      id: "consent",
      type: node_type.CONSENT,
    },
    {
      id: "instructions",
      type: node_type.INSTRUCTIONS,
      title: "Task Instructions",
      config: {
        component: "instructions",
      },
    },
    {
      id: "trial",
      type: node_type.TRIAL,
      config: {
        meta: {
          trial_component: "BlindSudokuTrial",
          show_points: true,
          stimuli: {
            source: "../../experiment-definitions/blind-sudoku/stimuli.json",
            presentation_mode: "random",
            trial_count: 5,
            selection_strategy: "random",
          },
          trial_type: "sudoku",
          time_limit: 300,
        } as trial_meta,
      },
    },
    {
      id: "survey",
      type: node_type.SURVEY,
      config: {
        meta: {
          questions: [
            [
              {
                id: "game_experience",
                type: "dropdown",
                text: "Prior Game Experience",
                placeholder: "Prior Game Experience",
                options: [
                  { value: "0", label: "0 prior games" },
                  { value: "1-5", label: "1-5 prior games" },
                  { value: "5-50", label: "5-50 prior games" },
                  { value: "more-50", label: "More than 50 prior games" },
                ],
                required: true,
              },
            ],
          ],
        },
      },
    },
    {
      id: "upload",
      type: node_type.DATA_UPLOAD,
      config: {
        meta: {
          message: "saving your results...",
          upload_delay_seconds: 3,
        },
      },
    },
    {
      id: "prolific",
      type: node_type.PROLIFIC_REDIRECT,
      config: {
        meta: {
          completion_code: "C14PRD5S",
        },
      },
    },
  ],
  edges: [
    {
      id: "consent_to_instructions",
      from_node: "consent",
      to_node: "instructions",
    },
    {
      id: "instructions_to_trial",
      from_node: "instructions",
      to_node: "trial",
    },
    {
      id: "trial_to_survey",
      from_node: "trial",
      to_node: "survey",
    },
    {
      id: "survey_to_upload",
      from_node: "survey",
      to_node: "upload",
    },
    {
      id: "upload_to_prolific",
      from_node: "upload",
      to_node: "prolific",
    },
  ],
} as experiment_definition;

