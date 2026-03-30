/**
 * Game Primitives - Composable building blocks for puzzle games
 *
 * These primitives are mode-agnostic and can be used in both
 * freeplay and experiment contexts.
 */

// Core state management
export { useBoardState, type BoardStateReturn, type BoardStateOptions } from "./useBoardState.ts";

// Input patterns
export { useStateCycler, type StateCyclerReturn } from "./useStateCycler.ts";

// Solution validation
export {
  useSolutionChecker,
  create_bridge_encoder,
  type SolutionCheckerConfig,
  type SolutionCheckerReturn,
} from "./useSolutionChecker.ts";

// Data recording (freeplay + experiment)
export {
  useDataRecorder,
  type DataRecorderConfig,
  type DataRecorderReturn,
} from "./useDataRecorder.ts";

// Game session orchestration (shared between freeplay + daily)
export {
  useGameSession,
  type GameSessionServices,
  type GameSessionConfig,
  type GameSessionReturn,
} from "./useGameSession.ts";

// Mode dispatcher (freeplay vs daily)
export { useGameForMode } from "./useGameForMode.ts";

// Demo/test game controller (no api, no persistence)
export { useDemoGame } from "./useDemoGame.ts";

// Cell interaction patterns
export { useCellDragHandlers } from "./useCellDragHandlers.ts";

// Violation checking utilities
export {
  ORTHOGONAL_DIRECTIONS,
  ALL_DIRECTIONS,
  count_adjacent,
  count_in_row,
  count_in_col,
  weighted_sum_row,
  weighted_sum_col,
  all_cells_in_row,
  all_cells_in_col,
  get_region_cells,
  get_all_region_ids,
  get_region_at,
  same_region,
  count_in_region,
} from "./useViolationCheckers.ts";
