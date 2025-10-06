import type { RenderEvents } from "@/features/games.composables/setupPuzzleInteractionBridge.ts";
import { check_violation_rule } from "@/utils.ts";
import type { PuzzleController, PuzzleState } from "@/services/game/engines/types.ts";
import type { PuzzleStateSudoku } from "@/services/states.ts";

/**
 * Sudoku violation highlighting behavior
 * Handles visual feedback for rule violations (duplicates in row/col/box)
 */
export function useSudokuViolationHighlighter(ctrl: PuzzleController): Partial<RenderEvents> {
  return {
    getCellClasses(row: number, col: number): string[] {
      const RULES = ["row_duplicate_violation", "col_duplicate_violation", "box_duplicate_violation"];
      const classes: string[] = [];
      const state = ctrl.state_puzzle.value as PuzzleState<PuzzleStateSudoku>

      // Check for violations and add red border styling
      if (check_violation_rule(ctrl.state_puzzle.value.violations, row, col, RULES)) {
        if (state.definition.initial_state[row][col] === -1) {
          classes.push("text-red-500!")
        } else {
          classes.push("border-red-500!", "border-[2px]");
        }
      }




      return classes;
    },
  };
}
