import { computed, ref, readonly } from "vue";
import type { RenderEvents } from "@/features/games.composables/setupPuzzleInteractionBridge.ts";
import type { BoardEvents, Cell } from "@/features/games.components/board.interaction.ts";
import type { usePuzzleState } from "@/composables/usePuzzleState.ts";
import type { PuzzleStateSudoku } from "@/services/states.ts";
import { check_violation_rule } from "@/utils.ts";

export type SudokuSession = Awaited<ReturnType<typeof usePuzzleState>> & {
  state: { value: PuzzleStateSudoku };
};

/**
 * Sudoku highlighting behavior - handles row/col/box selection highlighting
 * This replaces the old createSudokuBehavior but fits the new behavior pair pattern
 */
export function useSudokuCellHighlighter(session: SudokuSession) {
  const subgridSize = computed(() => Math.sqrt(session.state.value.rows ?? 0));
  const activeCell = ref<{ row: number; col: number } | null>(null);

  // Helper functions
  const isRowSelected = (row: number) => activeCell.value?.row === row;
  const isColSelected = (col: number) => activeCell.value?.col === col;
  const isCellActive = (row: number, col: number) => activeCell.value?.row === row && activeCell.value?.col === col;
  const shouldHighlightCell = (row: number, col: number) => isRowSelected(row) || isColSelected(col) || isSquareSelected(row, col);
  const isPrefilled = (row: number, col: number) => session.state.value.board_initial[row * session.state.value.cols + col] !== 0;
  const isSquareSelected = (row: number, col: number) => {
    if (!activeCell.value) return false;
    const { row: activeRow, col: activeCol } = activeCell.value;
    return (
      Math.floor(activeRow / subgridSize.value) === Math.floor(row / subgridSize.value) &&
      Math.floor(activeCol / subgridSize.value) === Math.floor(col / subgridSize.value)
    );
  };


  // Input behavior
  const inputBehavior: Partial<BoardEvents> = {
    onCellClick(cell: Cell, _event: MouseEvent): boolean {
      if (!session.state.value) return false;
      if (isPrefilled(cell.row, cell.col)) return false; // Don't select prefilled cells
      activeCell.value = { row: cell.row, col: cell.col };
      return false; // Let other behaviors handle the actual cell interaction
    },

    onCellKeyDown(cell: Cell, event: KeyboardEvent): boolean {
      const key = event.key;

      // Handle Escape to clear selection
      // NOTE(james): the space works here, but it is technically an inter-behavior interaction
      // which should be better modeled by a composite behavior, instead of just this behavior also
      // handling it. But for now, this is simpler.
      if (key === "Escape" || key === " ") {
        activeCell.value = null;
        return true;
      }

      if (!session.state.value) return false;

      // Don't modify prefilled cells
      if (isPrefilled(cell.row, cell.col)) return false;

      const keyAsNumber = Number(key);

      // Handle number input
      if (!isNaN(keyAsNumber) && keyAsNumber >= 1 && keyAsNumber <= session.state.value.rows) {
        session.session.handle_cell_click(cell, 0, keyAsNumber);
        return true;
      }

      // Handle deletion
      if (key === "Backspace" || key === "Delete") {
        const index = cell.row * session.state.value.cols + cell.col;
        session.state.value.board[index] = 0;
        session.session.handle_cell_click(cell, 0, 0);
        return true;
      }

      return false;
    },
  };

  // Render behavior
  const renderBehavior: Partial<RenderEvents> = {
    getCellClasses(row: number, col: number): string[] {
      const classes: string[] = [];

      // Active cell border
      if (isCellActive(row, col)) classes.push("border-blue-500", "border-[0.5px]");

      // Violation styling
      if (check_violation_rule(session.state.value.violations, row, col, ["row_duplicate_violation", "col_duplicate_violation", "box_duplicate_violation"])) {
        classes.push("border-red-500!", "border-[1px]");
      }

      // Highlight background for related cells
      if (shouldHighlightCell(row, col) && !isCellActive(row, col)) classes.push("bg-slate-300");

      // Text color based on whether it's prefilled
      if (!isPrefilled(row, col)) classes.push("text-blue-600");

      return classes;
    },

    isCellVisible(_row: number, _col: number): boolean {
      return true;
    },

    isCellActive(row: number, col: number): boolean {
      return isCellActive(row, col);
    },
  };

  return {
    inputBehavior,
    renderBehavior,
    state: {
      activeCell: readonly(activeCell),
    },
    // Expose helper methods for external use
    clearActiveCell: () => activeCell.value = null,
    isCellActive,
    shouldHighlightCell,
    isPrefilled,
  };
}

/**
 * Convenience function to register Sudoku highlight behavior
 */
export function withSudokuBehaviors(session: SudokuSession, bridge: any) {
  const behavior = useSudokuCellHighlighter(session);
  bridge.addInputBehaviour(() => behavior.inputBehavior);
  bridge.addRenderBehaviour(() => behavior.renderBehavior);
  return behavior;
}
