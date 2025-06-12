import type { usePuzzleState } from "@/composables/usePuzzleState.ts";
import type { RenderEvents } from "@/features/games.composables/setupPuzzleInteractionBridge.ts";
import { computed, ref } from "vue";
import type { BoardEvents, Cell } from "@/features/games.components/board.interaction.ts";
import { type SudokuSession } from "@/features/games/sudoku/useSudokuCellHighlighter.ts";
import type { PuzzleStateSudoku } from "@/services/states.ts";

export function useSudokuFocusHighlighter(session: Awaited<ReturnType<typeof usePuzzleState>>) {
  // State
  const state = session.state.value as PuzzleStateSudoku;
  const lastHoveredCell = ref<Cell | null>(null);
  const lastSelectedHoveredCell = ref<Cell | null>(null);
  const subgridSize = computed(() => Math.sqrt(session.state.value.rows ?? 0));

  // Helper functions
  //// Hover Highlighting
  const isRowHovered = (row: number) => (lastHoveredCell.value ? lastHoveredCell.value.row === row : false);
  const isColHovered = (col: number) => (lastHoveredCell.value ? lastHoveredCell.value.col === col : false);
  const shouldHoverHighlight = (row: number, col: number) =>
    isRowHovered(row) || isColHovered(col) || isBoxHovered(row, col);
  const isBoxHovered = (row: number, col: number) => {
    if (!lastHoveredCell.value) return false;
    const { row: hovered_row, col: hovered_col } = lastHoveredCell.value;
    return (
      Math.floor(hovered_row / subgridSize.value) === Math.floor(row / subgridSize.value) &&
      Math.floor(hovered_col / subgridSize.value) === Math.floor(col / subgridSize.value)
    );
  };
  //// Selection Visibility
  const isRowSelected = (row: number) =>
    lastSelectedHoveredCell.value ? lastSelectedHoveredCell.value.row === row : false;
  const isColSelected = (col: number) =>
    lastSelectedHoveredCell.value ? lastSelectedHoveredCell.value.col === col : false;
  const isBoxSelected = (row: number, col: number) => {
    if (!lastSelectedHoveredCell.value) return false;
    const { row: selectedRow, col: selectedCol } = lastSelectedHoveredCell.value;
    return (
      Math.floor(selectedRow / subgridSize.value) === Math.floor(row / subgridSize.value) &&
      Math.floor(selectedCol / subgridSize.value) === Math.floor(col / subgridSize.value)
    );
  };
  const shouldShowCell = (row: number, col: number) =>
    isRowSelected(row) || isColSelected(col) || isBoxSelected(row, col);

  const renderBehavior: Partial<RenderEvents> = {
    getCellContent(row: number, col: number): string | number | null {
      const idx = row * session.state.value.cols + col;
      const value = session.state.value.board[idx];
      if (!shouldShowCell(row, col)) return value === 0 ? "" : "X";

      // If you have is_prefilled, use it here. Otherwise, just show value if not zero.
      return value !== 0 ? value : "";
    },
    getCellClasses(row: number, col: number): string[] {
      const classes: string[] = ["blur-[1.5px]", "overflow-hidden"];
      if (shouldHoverHighlight(row, col)) classes.push("bg-yellow-200");
      if (shouldShowCell(row, col)) {
        const blurIdx = classes.indexOf("blur-[1.5px]");
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
