import { computed, readonly, ref } from "vue";
import type { RenderEvents } from "@/features/games.composables/setupPuzzleInteractionBridge.ts";
import type { BoardEvents, Cell } from "@/features/games.components/board.interaction.ts";
import type { PuzzleStateSudoku } from "@/services/states.ts";
import { check_violation_rule } from "@/utils.ts";
import { isCellMatch } from "@/features/games/sudoku/sudoku.utility.ts";
import type { PuzzleController } from "@/services/game/engines/types.ts";

export type SudokuSession = {
  state: { value: PuzzleStateSudoku };
};

/**
 * Sudoku highlighting behavior - handles row/col/box selection highlighting
 * This replaces the old createSudokuBehavior but fits the new behavior pair pattern
 */
export function useSudokuCellHighlighter(ctrl: PuzzleController) {
  const enabled = ref(true); // Enable/disable highlighting behavior
  const setEnabled = (value: boolean) => (enabled.value = value);

  const showCorrectCells = ref(false); // Show correct cells (for testing/debugging)
  const setShowCorrectCells = (value: boolean) => (showCorrectCells.value = value);

  const subgridSize = computed(() => {
    const rows = ctrl.state_puzzle.value.definition.rows;
    return rows ? Math.sqrt(rows) : 3;
  });
  const activeCell = ref<Cell | null>(null);
  // Helper functions
  const activeMatch = (row: number, col: number) => isCellMatch(activeCell.value, row, col, subgridSize.value);
  const shouldHighlightCell = (row: number, col: number) => {
    const match = activeMatch(row, col);
    return match.row || match.col || match.box;
  };
  const isCellActive = (row: number, col: number) => activeCell.value?.row === row && activeCell.value?.col === col;
  const isPrefilled = (row: number, col: number) => ctrl.state_puzzle.value.definition.initial_state[row][col] !== -1;

  // Input behavior
  const inputBehavior: Partial<BoardEvents> = {
    onCellMouseDown(cell: Cell, _event: MouseEvent): boolean {
      if (!enabled.value) return false;
      activeCell.value = cell;
      return false; // Let other behaviors handle the actual cell interaction
    },

    onCellKeyDown(cell: Cell, event: KeyboardEvent): boolean {
      const key = event.key;
      if (!activeCell.value) return false; // No active cell to handle

      // Handle Escape to clear selection
      // NOTE(james): the space works here, but it is technically an inter-behavior interaction
      // which should be better modeled by a composite behavior, instead of just this behavior also
      // handling it. But for now, this is simpler.
      if (key === "Escape") {
        activeCell.value = null;
        return true;
      }

      const keyAsNumber = Number(key);

      // Handle number input
      if (!isNaN(keyAsNumber) && keyAsNumber >= 1 && keyAsNumber <= ctrl.state_puzzle.value.definition.rows) {
        ctrl.handle_cell_key_down(activeCell.value, event, key);
        return true;
      }

      // Handle deletion
      if (key === "Backspace" || key === "Delete") {
        ctrl.state_puzzle.value.board[activeCell.value.row][activeCell.value.col] = 0;
        ctrl.handle_cell_key_down(activeCell.value, event, 0);
        return true;
      }

      return false;
    },
  };

  // Render behavior
  const renderBehavior: Partial<RenderEvents> = {
    isCellActive,
    isCellVisible(_row: number, _col: number): boolean {
      return true;
    },
    getCellClasses(row: number, col: number): string[] {
      const is_prefilled = isPrefilled(row, col);
      const classes: string[] = [];
      // Only add styling if we have a valid state with violations data

      const is_violation = check_violation_rule(ctrl.state_puzzle.value.violations, row, col, [
        "row_duplicate_violation",
        "col_duplicate_violation",
        "box_duplicate_violation",
      ]);

      if (isCellActive(row, col)) classes.push("bg-slate-300!"); // Active cell border
      if (shouldHighlightCell(row, col)) classes.push("bg-slate-200!"); // Highlight background for related cells
      if (!is_prefilled) {
        classes.push("text-sky-600!");
      } // Text color based on whether it's prefilled

      // Violation styling - only add if not prefilled
      if (showCorrectCells.value && !is_prefilled) {
        if (is_violation) {
          classes.push("bg-red-100");
        } else {
          classes.push("bg-green-100");
        }
      }

      return classes;
    },
  };

  return {
    inputBehavior,
    renderBehavior,
    state: { activeCell: readonly(activeCell) },
    // Expose helper methods for external use
    clearActiveCell: () => (activeCell.value = null),
    isCellActive,
    shouldHighlightCell,
    setShowCorrectCells,
    isPrefilled,
    setEnabled,
  };
}

/**
 * Convenience function to register Sudoku highlight behavior
 */
export function withSudokuBehaviors(controller: PuzzleController, bridge: any) {
  const behavior = useSudokuCellHighlighter(controller);
  bridge.addInputBehaviour(() => behavior.inputBehavior);
  bridge.addRenderBehaviour(() => behavior.renderBehavior);
  return behavior;
}
