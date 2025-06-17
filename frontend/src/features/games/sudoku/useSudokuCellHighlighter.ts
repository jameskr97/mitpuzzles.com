import { computed, ref, readonly } from "vue";
import type { RenderEvents } from "@/features/games.composables/setupPuzzleInteractionBridge.ts";
import type { BoardEvents, Cell } from "@/features/games.components/board.interaction.ts";
import type { PuzzleStateSudoku } from "@/services/states.ts";
import { check_violation_rule } from "@/utils.ts";
import type { createPuzzleSession } from "@/composables/useCurrentPuzzle.ts";
import { isCellMatch } from "@/features/games/sudoku/sudoku.utility.ts";

export type SudokuSession = Awaited<ReturnType<typeof createPuzzleSession>> & {
  state: { value: PuzzleStateSudoku };
};

/**
 * Sudoku highlighting behavior - handles row/col/box selection highlighting
 * This replaces the old createSudokuBehavior but fits the new behavior pair pattern
 */
export function useSudokuCellHighlighter(session: SudokuSession) {
  const subgridSize = computed(() => {
    const rows = session.state.value?.rows;
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
  const isPrefilled = (row: number, col: number) => session.state.value?.board_initial[row * session.state.value?.cols + col] !== 0;


  // Input behavior
  const inputBehavior: Partial<BoardEvents> = {
    onCellClick(cell: Cell, _event: MouseEvent): boolean {
      if (!session.state.value) return false;
      activeCell.value = cell
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
      // if (isPrefilled(cell.row, cell.col)) return false; // Don't modify prefilled cells

      const keyAsNumber = Number(key);

      // Handle number input
      if (!isNaN(keyAsNumber) && keyAsNumber >= 1 && keyAsNumber <= session.state.value.rows) {
        session.interact.handle_cell_click(cell, 0, keyAsNumber);
        return true;
      }

      // Handle deletion
      if (key === "Backspace" || key === "Delete") {
        const index = cell.row * session.state.value.cols + cell.col;
        session.state.value.board[index] = 0;
        session.interact.handle_cell_click(cell, 0, 0);
        return true;
      }

      return false;
    },
  };

  // Render behavior
  const renderBehavior: Partial<RenderEvents> = {
    isCellActive,
    isCellVisible(_row: number, _col: number): boolean { return true },
    getCellClasses(row: number, col: number): string[] {
      const classes: string[] = [];
      if (isCellActive(row, col))         classes.push('bg-slate-300!'); // Active cell border
      if (shouldHighlightCell(row, col))  classes.push("bg-slate-200!"); // Highlight background for related cells
      if (!isPrefilled(row, col))         classes.push("text-sky-600!"); // Text color based on whether it's prefilled

      // Violation styling
      if (session.state.value?.violations && check_violation_rule(session.state.value.violations, row, col, ["row_duplicate_violation", "col_duplicate_violation", "box_duplicate_violation"]))
        classes.push("border-red-500!", "border-[1px]");
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
