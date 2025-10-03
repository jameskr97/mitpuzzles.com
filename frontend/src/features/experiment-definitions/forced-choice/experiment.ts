import { type experiment_definition, node_type } from "@/features/experiment-core";
import type { trial_meta } from "@/features/experiment-core/graph/types.ts";
import type { raw_stimuli } from "@/features/experiment-core/stimuli/types.ts";

// import all minesweeper files
import minesweeper_easy_easy from "./minesweeper_3x3_easy_easy.json";
import minesweeper_easy_hard from "./minesweeper_3x3_easy_hard.json";
import minesweeper_hard_hard from "./minesweeper_3x3_hard_hard.json";

// callback function to load all minesweeper stimuli
function load_all_minesweeper_stimuli(): raw_stimuli {
  const all_stimuli = [
    ...minesweeper_easy_easy,
    ...minesweeper_easy_hard,
    ...minesweeper_hard_hard
  ];
  return all_stimuli;
}

// check if visitor is from prolific (has PROLIFIC_PID URL parameter)
const is_prolific_visitor = new URLSearchParams(window.location.search).has("PROLIFIC_PID");

export default {
  id: "forced-choice",
  title: "Forced Choice",
  description: "Experiment where participants are forced to choose between puzzles.",
  entry_node: is_prolific_visitor ? "consent" : "instructions", // skip consent for direct visitors
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
          trial_component: "ForcedChoiceTrial",
          show_points: false,
          stimuli: {
            source: load_all_minesweeper_stimuli,
            presentation_mode: "random",
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
              {
                id: "board_selection",
                type: "dropdown",
                text: "Which boards did you try to select?",
                placeholder: "Select board preference",
                options: [
                  { value: "easy", label: "Easy" },
                  { value: "hard", label: "Hard" },
                  { value: "no_preference", label: "No preference" },
                ],
                other_option: { label: "Other", has_input: true },
                required: true,
              },
            ],
            [
              {
                id: "decision_motivation",
                type: "textarea",
                text: "What motivated your decision in choosing the puzzle?",
                placeholder: "Describe what influenced your puzzle selection...",
                description: "Please explain the reasoning behind your puzzle choice.",
                rows: 4,
                required: true,
              },
              {
                id: "selection_factors",
                type: "multiple_choice",
                text: "What factors went into your board selection?",
                max_selections: 2,
                options: [
                  { value: "solved_in_head", label: "I partially solved one or both games in my head" },
                  { value: "big_numbers", label: "Big numbers" },
                  { value: "small_numbers", label: "Small numbers" },
                  { value: "few_unknown", label: "Few unknown squares" },
                  { value: "many_unknown", label: "Many unknown squares" },
                ],
                other_option: { has_input: true },
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
          completion_code: "CTTPFQGV",
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

