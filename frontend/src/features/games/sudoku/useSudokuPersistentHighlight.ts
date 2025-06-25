import type { RenderEvents } from "@/features/games.composables/setupPuzzleInteractionBridge.ts";
import type { PuzzleStateSudoku } from "@/services/states.ts";
import type { createPuzzleSession } from "@/composables/useCurrentPuzzle.ts";
import { computed } from "vue";

export type SudokuSession = Awaited<ReturnType<typeof createPuzzleSession>> & {
  state: { value: PuzzleStateSudoku };
};

export interface PersistentHighlightOptions {
  row?: number;
  col?: number;
  box?: number;
  cells?: { row: number; col: number }[];
  cell_class?: string;
}

/**
 * Sudoku highlighting behavior - handles persistent row/col/box highlighting
 */
export function useSudokuPersistentHighlighter(session: SudokuSession, options?: PersistentHighlightOptions) {
  const highlightOptions = {
    row: options?.row ?? -1,
    col: options?.col ?? -1,
    box: options?.box ?? -1,
    cells: options?.cells ?? [],
    cell_class: options?.cell_class ?? "bg-blue-400!",
  };
  const subgridSize = computed(() => Math.sqrt(session.state.value?.board_initial.length || 9));

  // Render behavior
  const renderBehavior: Partial<RenderEvents> = {
    getCellClasses(row: number, col: number): string[] {
      const classes: string[] = [];
      let shouldHighlightPosition = false;
      if (highlightOptions.row >= 0 && highlightOptions.row === row) shouldHighlightPosition = true;
      if (highlightOptions.col >= 0 && highlightOptions.col === col) shouldHighlightPosition = true;
      if (highlightOptions.box >= 0) {
        const boxSize = subgridSize.value;
        const boxRow = Math.floor(row / boxSize);
        const boxCol = Math.floor(col / boxSize);
        const boxIndex = boxRow * boxSize + boxCol;
        if (boxIndex === highlightOptions.box) shouldHighlightPosition = true;
      }

      if (shouldHighlightPosition) classes.push("bg-red-400");
      // Check for specific cell highlights (border)
      if (highlightOptions.cells && highlightOptions.cells.length > 0)
        if (highlightOptions.cells.some((cell) => cell.row === row && cell.col === col))
          classes.push(highlightOptions.cell_class);
      return classes;
    },
  };

  return {
    renderBehavior,
  };
}

/**
 * Convenience function to register Sudoku highlight behavior
 */
export function withSudokuPersistentHighlighter(
  session: SudokuSession,
  bridge: any,
  persistentOptions?: PersistentHighlightOptions,
) {
  const behavior = useSudokuPersistentHighlighter(session, persistentOptions);
  bridge.addRenderBehaviour(() => behavior.renderBehavior);
  return behavior;
}
