import type { usePuzzleState } from "../../../../../.private/usePuzzleState.ts";
import type { RenderEvents } from "@/features/games.composables/setupPuzzleInteractionBridge.ts";
import { computed, ref } from "vue";
import type { BoardEvents, Cell } from "@/features/games.components/board.interaction.ts";
import { type SudokuSession } from "@/features/games/sudoku/useSudokuCellHighlighter.ts";
import { isCellMatch } from "@/features/games/sudoku/sudoku.utility.ts";

export function useSudokuFocusHighlighter(session: Awaited<ReturnType<typeof usePuzzleState>>) {
  // State
  const lastHoveredCell = ref<Cell | null>(null);
  const lastSelectedHoveredCell = ref<Cell | null>(null);
  const subgridSize = computed(() => Math.sqrt(session.state.value.rows ?? 0));

  // Helper functions
  //// Hover Highlighting
  const hoverMatch = (row: number, col: number) => isCellMatch(lastHoveredCell.value, row, col, subgridSize.value);
  const shouldHoverHighlight = (row: number, col: number) => {
    const match = hoverMatch(row, col);
    return match.row || match.col || match.box;
  };

  //// Selection Visibility
  const selectedMatch = (row: number, col: number) =>
    isCellMatch(lastSelectedHoveredCell.value, row, col, subgridSize.value);
  const shouldShowCell = (row: number, col: number) => {
    const match = selectedMatch(row, col);
    return match.row || match.col || match.box;
  };

  const renderBehavior: Partial<RenderEvents> = {
    getCellContent(row: number, col: number): string | number | null {
      const idx = row * session.state.value.cols + col;
      const value = session.state.value.board[idx];
      if (!shouldShowCell(row, col)) return value === 0 ? "" : "X";

      // If you have is_prefilled, use it here. Otherwise, just show value if not zero.
      return value !== 0 ? value : "";
    },
    getCellClasses(row: number, col: number): string[] {
      const BLUR_CLASS = "blur-[1.5px]";
      const classes: string[] = [BLUR_CLASS, "overflow-hidden"];
      if (shouldHoverHighlight(row, col)) classes.push("bg-yellow-50");
      if (shouldShowCell(row, col)) {
        const blurIdx = classes.indexOf(BLUR_CLASS);
        if (blurIdx !== -1) classes.splice(blurIdx, 1);
      }
      return classes;
    },
  };

  const inputBehavior: Partial<BoardEvents> = {
    onCellEnter(cell: Cell, _event: MouseEvent): boolean {
      lastHoveredCell.value = cell;
      return false;
    },
    onKeyDown(event: KeyboardEvent): boolean {
      event.preventDefault(); // Prevent default browser behavior
      const key = event.key;
      if (key === "Escape") {
        lastHoveredCell.value = null;
        lastSelectedHoveredCell.value = null;
        return true; // Clear selection
      }
      return false; // Let other behaviors handle the key
    },

    onBoardLeave(_event: MouseEvent): boolean {
      lastHoveredCell.value = null;
      return false;
    },
    onCellHoveredKeyDown(cell: Cell, event: KeyboardEvent): boolean {
      const key = event.key;
      if (key === " ") lastSelectedHoveredCell.value = cell;
      return false;
    },
  };

  return {
    inputBehavior,
    renderBehavior,
  };
}

export function withSudokuFocusBehavior(session: SudokuSession, bridge: any) {
  const behavior = useSudokuFocusHighlighter(session);
  bridge.addInputBehaviour(() => behavior.inputBehavior);
  bridge.addRenderBehaviour(() => behavior.renderBehavior);
  return behavior;
}
