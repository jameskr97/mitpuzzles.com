import type { PuzzleDefinition } from "@/services/game/engines/types";

/**
 * stimuli presentation modes
 *
 * Controls how the TrialNode presents loaded stimuli to the user:
 *
 * - 'sequential': Show one puzzle at a time
 *   - For sequential data: [A], [B], [C] → shows A, then B, then C
 *   - For paired data: [A,B], [C,D] → flattens to A, then B, then C, then D
 *
 * - 'paired': Show two puzzles side-by-side simultaneously
 *   - For sequential data: [A], [B], [C] → pairs them as [A,B], [C,null]
 *   - For paired data: [A,B], [C,D] → shows A&B together, then C&D together
 *
 * - 'random': Randomly select one puzzle from each pair
 *   - For sequential data: [A], [B], [C] → shows A, then B, then C (no change)
 *   - For paired data: [A,B], [C,D] → randomly picks A or B, then C or D
 */
export type presentation_mode = "sequential" | "paired" | "random";

/**
 * strategy for selecting stimuli from available set
 */
export type selection_strategy = "first_n" | "random" | "balanced";

/**
 * supported stimuli formats
 */
export type stimuli_format = "sequential_list" | "paired_list";

/**
 * raw stimuli data - either single puzzles or pairs
 */
export type raw_stimuli = PuzzleDefinition[] | PuzzleDefinition[][];

/**
 * stimuli source - either a file path or a callback function that returns stimuli
 */
export type stimuli_source = string | (() => raw_stimuli | Promise<raw_stimuli>);

/**
 * processed stimuli ready for presentation
 */
export interface processed_stimuli {
  format: stimuli_format;
  items: PuzzleDefinition[][]; // always pairs, single items become [item]
  total_count: number;
}

/**
 * configuration for loading and presenting stimuli
 */
export interface stimuli_config {
  source: stimuli_source; // path to stimuli file or callback function
  presentation_mode: presentation_mode;
  trial_count?: number; // if not specified, use all available
  selection_strategy: selection_strategy;
}
