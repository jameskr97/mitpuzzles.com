import { computed, readonly, ref } from "vue";
import type { RenderEvents } from "@/features/games.composables/setupPuzzleInteractionBridge.ts";
import type { BoardEvents, Cell } from "@/features/games.components/board.interaction.ts";
import type { PuzzleStateSudoku } from "@/services/states.ts";
import { check_violation_rule } from "@/utils.ts";
import { isCellMatch } from "@/features/games/sudoku/sudoku.utility.ts";
import type { usePuzzleController } from "@/composables/usePuzzleController.ts";

export type SudokuSession = {
  state: { value: PuzzleStateSudoku };
};

/**
 * Sudoku highlighting behavior - handles row/col/box selection highlighting
 * This replaces the old createSudokuBehavior but fits the new behavior pair pattern
 */
export function useSudokuCellHighlighter(ctrl: ReturnType<typeof usePuzzleController>) {
  const enabled = ref(true); // Enable/disable highlighting behavior
  const setEnabled = (value: boolean) => (enabled.value = value);

  const showCorrectCells = ref(false); // Show correct cells (for testing/debugging)
  const setShowCorrectCells = (value: boolean) => (showCorrectCells.value = value);

  const subgridSize = computed(() => {
    const rows = ctrl.state.value?.rows;
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
  const isPrefilled = (row: number, col: number) =>
    ctrl.state.value?.board_initial[row * ctrl.state.value?.cols + col] !== 0;

  // Input behavior
  const inputBehavior: Partial<BoardEvents> = {
    onCellMouseDown(cell: Cell, _event: MouseEvent): boolean {
      if (!enabled.value) return false;
      if (!ctrl.state.value) return false;
      activeCell.value = cell;
      return false; // Let other behaviors handle the actual cell interaction
    },

    onCellKeyDown(cell: Cell, event: KeyboardEvent): boolean {
      const key = event.key;

      // Handle Escape to clear selection
      // NOTE(james): the space works here, but it is technically an inter-behavior interaction
      // which should be better modeled by a composite behavior, instead of just this behavior also
      // handling it. But for now, this is simpler.
      if (key === "Escape") {
        activeCell.value = null;
        return true;
      }

      if (!ctrl.state.value) return false;
      // if (isPrefilled(cell.row, cell.col)) return false; // Don't modify prefilled cells

      const keyAsNumber = Number(key);

      // Handle number input
      if (!isNaN(keyAsNumber) && keyAsNumber >= 1 && keyAsNumber <= ctrl.state.value.rows) {
        ctrl.handleCellClick(activeCell.value, 0, keyAsNumber);
        return true;
      }

      // Handle deletion
      if (key === "Backspace" || key === "Delete") {
        const index = cell.row * ctrl.state.value.cols + cell.col;
        ctrl.state.value.board[index] = 0;
        ctrl.handleCellClick(cell, 0, 0);
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
      const is_violation =
        ctrl.state.value?.violations &&
        check_violation_rule(ctrl.state.value.violations, row, col, [
          "row_duplicate_violation",
          "col_duplicate_violation",
          "box_duplicate_violation",
        ]);
      const is_prefilled = isPrefilled(row, col);
      const classes: string[] = [];
      if (showCorrectCells.value && !is_violation && !is_prefilled) classes.push("bg-green-100"); // Highlight correct cells
      if (isCellActive(row, col)) classes.push("bg-slate-300!"); // Active cell border
      if (shouldHighlightCell(row, col)) classes.push("bg-slate-200!"); // Highlight background for related cells
      if (!isPrefilled(row, col)) classes.push("text-sky-600!"); // Text color based on whether it's prefilled

      // Violation styling
      if (!is_prefilled && is_violation) {
        classes.push("bg-red-100!");
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
export function withSudokuBehaviors(session: ReturnType<typeof usePuzzleController>, bridge: any) {
  const behavior = useSudokuCellHighlighter(session);
  bridge.addInputBehaviour(() => behavior.inputBehavior);
  bridge.addRenderBehaviour(() => behavior.renderBehavior);
  return behavior;
}
