/**
 * GameController Interface
 *
 * Minimal interface that games expose for shared UI components (statusbar, leaderboard, etc.)
 * Games own their complete logic - this interface just defines what shared UI needs.
 */
import type { ComputedRef, Ref } from "vue";
import type { PuzzleVariant } from "@/core/types";

/**
 * Core puzzle definition info that shared UI needs
 * Note: size/difficulty come from current_variant, not the definition
 */
export interface GameDefinition {
  id: string;
  puzzle_type: string;
  rows: number;
  cols: number;
}

/**
 * Game state exposed to shared UI
 */
export interface GameState {
  solved: boolean;
  definition: GameDefinition;
}

/**
 * UI state for animations and visual feedback
 */
export interface GameUIState {
  show_solved_state: boolean;
  tutorial_mode: boolean;
  animate_success: boolean;
  animate_failure: boolean;
}

/**
 * Minimal interface for shared UI components
 *
 * Games implement this to work with GameLayout, StatusBar, Leaderboard, etc.
 * Games can extend this with their own properties/methods.
 */
export interface GameController {
  // Identity
  puzzle_type: string;

  // State (readonly for shared UI)
  state: ComputedRef<GameState>;
  ui: Ref<GameUIState>;

  // Variant tracking (for leaderboard, new puzzle)
  current_variant: Ref<PuzzleVariant>;

  // Whether tutorial was used (affects leaderboard eligibility)
  tutorial_used: Ref<boolean>;

  // Timer
  formatted_time: ComputedRef<string>;

  // Core actions that shared UI can trigger
  check_solution: () => Promise<boolean>;
  clear_puzzle: () => void;
  request_new_puzzle: () => Promise<void>;

  // optional — if present, game requires explicit start (e.g. daily)
  start_game?: () => Promise<void>;

  // optional — marks this as a demo/test game with no backend puzzles
  is_demo?: boolean;
}
