import type { RenderEvents } from "@/features/games.composables/setupPuzzleInteractionBridge.ts";
import { computed, ref } from "vue";
import type { BoardEvents, Cell } from "@/features/games.components/board.interaction.ts";
import { isCellMatch } from "@/features/games/sudoku/sudoku.utility.ts";
import type { PuzzleController } from "@/services/game/engines/types.ts";
import type { HistoryMode } from "@/store/database";
import { useGameHistoryStore } from "@/store/useGameHistoryStore.ts";
import { useExperimentContext } from "@/features/experiments/core/useExperimentContext.ts";

export function useSudokuFocusHighlighter(ctrl: PuzzleController) {
  const enabled = ref(true); // Enable/disable highlighting behavior
  const setEnabled = (value: boolean) => (enabled.value = value);
  const shouldRecordFocus = ref<HistoryMode | null>(null); // Whether to record focus in history
  const setShouldRecordFocus = (value: HistoryMode | null) => (shouldRecordFocus.value = value);
  const historyStore = useGameHistoryStore();
  const context = useExperimentContext()

  // State
  const lastRecordedFocus = ref<Cell | null>(null);
  const lastHoveredCell = ref<Cell | null>(null);
  const lastSelectedHoveredCell = ref<Cell | null>(null);
  const subgridSize = computed(() => {
    const rows = ctrl.state_puzzle.value.definition.rows;
    return rows ? Math.sqrt(rows) : 3;
  });

  const reset_selected_hovered_cell = () => {
    lastSelectedHoveredCell.value = null;
    lastHoveredCell.value = null;
  };

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
      const value = ctrl.state_puzzle.value.board[row][col] || 0;
      if (!enabled.value) return value === 0 ? "" : value;
      if (!shouldShowCell(row, col)) return value === 0 ? "" : "X";

      // If you have is_prefilled, use it here. Otherwise, just show value if not zero.
      return value !== 0 ? value : "";
    },

    getCellClasses(row: number, col: number): string[] {
      if (!enabled.value) return [];
      const BLUR_CLASS = "blur-[5px]";
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
      if (!enabled.value) return true;

      lastHoveredCell.value = cell;
      return false;
    },
    onKeyDown(event: KeyboardEvent): boolean {
      if (!enabled.value) return true;
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
      if (!enabled.value) return true;
      lastHoveredCell.value = null;
      return false;
    },
    onCellClick(cell: Cell, event: MouseEvent): boolean {
      if (!enabled.value) return true;
      lastSelectedHoveredCell.value = cell;
      const { row, col } = lastSelectedHoveredCell.value;
      const { row: rowR, col: colR } = lastRecordedFocus.value || {};
      const are_same = row === rowR && col === colR;
      if (shouldRecordFocus.value !== null && !are_same) {
        lastRecordedFocus.value = cell;
        // Record the focus event in history
        historyStore.addExperimentEvent(context.getExperimentData().experimentId, context.getCurrentTrialInfo().trialId, "sudoku", {
          action: "focus",
          cell: { row: cell.row, col: cell.col },
          timestamp: Date.now(),
        });
      }
      return false;
    },
  };

  return {
    inputBehavior,
    renderBehavior,
    setEnabled,
    setShouldRecordFocus,
    reset_selected_hovered_cell,
  };
}

export function withSudokuFocusBehavior(ctrl: PuzzleController, bridge: any) {
  const behavior = useSudokuFocusHighlighter(ctrl);
  bridge.addInputBehaviour(() => behavior.inputBehavior);
  bridge.addRenderBehaviour(() => behavior.renderBehavior);
  return behavior;
}
