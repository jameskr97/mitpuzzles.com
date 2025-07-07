import type { RenderEvents } from "@/features/games.composables/setupPuzzleInteractionBridge.ts";
import { check_violation_rule } from "@/utils.ts";
import type { PuzzleController } from "@/services/game/engines/types.ts";

/**
 * Sudoku violation highlighting behavior
 * Handles visual feedback for rule violations (duplicates in row/col/box)
 */
export function useSudokuViolationHighlighter(ctrl: PuzzleController): Partial<RenderEvents> {
  return {
    getCellClasses(row: number, col: number): string[] {
      const classes: string[] = [];

      // Check for violations and add red border styling
      if (
        check_violation_rule(ctrl.state_puzzle.value.violations, row, col, [
          "row_duplicate_violation",
          "col_duplicate_violation",
          "box_duplicate_violation",
        ])
      ) {
        classes.push("border-red-500!", "border-[1px]");
      }

      return classes;
    },
  };
}
