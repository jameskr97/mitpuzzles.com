import type { RenderEvents } from "@/features/games.composables/setupPuzzleInteractionBridge.ts";
import type { PuzzleStateSudoku } from "@/services/states.ts";
import { computed } from "vue";
import type { PuzzleState } from "@/services/game/engines/types.ts";

export interface PersistentHighlightOptions {
  row?: number;
  col?: number;
  box?: number;
  highlight_cells?: { row: number; col: number; classStyle: string }[];
  specific_cell_class?: { row: number; col: number; classStyle: string }[];
  cells?: { row: number; col: number }[];
  cell_class?: string;
}

/**
 * Sudoku highlighting behavior - handles persistent row/col/box highlighting
 */
export function useSudokuPersistentHighlighter(board: PuzzleState, options?: PersistentHighlightOptions) {
  const highlightOptions = {
    row: options?.row ?? -1,
    col: options?.col ?? -1,
    box: options?.box ?? -1,
    cells: options?.cells ?? [],
    highlight_cells: options?.highlight_cells ?? [],
    specific_cell_class: options?.specific_cell_class ?? [],
    cell_class: options?.cell_class ?? "",
  };
  const subgridSize = computed(() => Math.sqrt(board.definition.rows || 9));

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

      if (highlightOptions.highlight_cells && highlightOptions.highlight_cells.length > 0) {
        const cellHighlight = highlightOptions.highlight_cells.find((cell) => cell.row === row && cell.col === col);
        if (cellHighlight) classes.push(cellHighlight.classStyle);
      }
      if (highlightOptions.specific_cell_class && highlightOptions.specific_cell_class.length > 0) {
        const specificCell = highlightOptions.specific_cell_class.find((cell) => cell.row === row && cell.col === col);
        if (specificCell) classes.push(specificCell.classStyle);
      }

      if (shouldHighlightPosition) classes.push("bg-yellow-200");
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
  board: PuzzleState,
  bridge: any,
  persistentOptions?: PersistentHighlightOptions,
) {
  const behavior = useSudokuPersistentHighlighter(board, persistentOptions);
  bridge.addRenderBehaviour(() => behavior.renderBehavior);
  return behavior;
}
