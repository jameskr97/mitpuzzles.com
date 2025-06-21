import { computed, readonly, ref } from "vue";
import type { RenderEvents } from "@/features/games.composables/setupPuzzleInteractionBridge.ts";
import type { BoardEvents } from "@/features/games.components/board.interaction.ts";
import type { PuzzleController } from "@/services/game/engines/types.ts";

export type CellValidationState = "correct" | "incorrect" | "neutral";

export interface ValidationCell {
  row: number;
  col: number;
  state: CellValidationState;
}

/**
 * Sudoku validation highlighting behavior - handles marking cells as correct/incorrect
 * with green/red background colors
 */
export function useSudokuValidationHighlighter(ctrl: PuzzleController) {
  const enabled = ref(true);
  const setEnabled = (value: boolean) => (enabled.value = value);

  // Store validation states for each cell
  const validationStates = ref<Map<string, CellValidationState>>(new Map());

  // Helper to create cell key
  const getCellKey = (row: number, col: number) => `${row}-${col}`;

  // Helper to get validation state for a cell
  const getCellValidationState = (row: number, col: number): CellValidationState => {
    return validationStates.value.get(getCellKey(row, col)) || "neutral";
  };

  // Set a single cell as incorrect
  const setIncorrect = (row: number, col: number) => {
    validationStates.value.set(getCellKey(row, col), "incorrect");
  };

  // Set a single cell as correct
  const setCorrect = (row: number, col: number) => {
    validationStates.value.set(getCellKey(row, col), "correct");
  };

  // Set a single cell as neutral (no highlighting)
  const setNeutral = (row: number, col: number) => {
    validationStates.value.set(getCellKey(row, col), "neutral");
  };

  // Bulk operations
  const setMultipleIncorrect = (cells: Array<{ row: number; col: number }>) => {
    cells.forEach((cell) => setIncorrect(cell.row, cell.col));
  };

  const setMultipleCorrect = (cells: Array<{ row: number; col: number }>) => {
    cells.forEach((cell) => setCorrect(cell.row, cell.col));
  };

  // Clear all validation states
  const clearAll = () => {
    validationStates.value.clear();
  };

  // Clear specific cell
  const clearCell = (row: number, col: number) => {
    validationStates.value.delete(getCellKey(row, col));
  };

  // Get all cells with a specific state
  const getCellsWithState = (state: CellValidationState): Array<{ row: number; col: number }> => {
    const cells: Array<{ row: number; col: number }> = [];
    validationStates.value.forEach((cellState, key) => {
      if (cellState === state) {
        const [row, col] = key.split("-").map(Number);
        cells.push({ row, col });
      }
    });
    return cells;
  };

  // Helper to check if cell is prefilled
  const isPrefilled = (row: number, col: number) => ctrl.state_puzzle.value.definition.initial_state[row][col] !== -1;

  // Input behavior - minimal, mainly for potential future interactions
  const inputBehavior: Partial<BoardEvents> = {
    // Could add click handlers here if needed for manual validation
  };

  // Render behavior
  const renderBehavior: Partial<RenderEvents> = {
    getCellClasses(row: number, col: number): string[] {
      if (!enabled.value) return [];

      const classes: string[] = [];
      const validationState = getCellValidationState(row, col);

      // Apply validation styling based on state
      switch (validationState) {
        case "correct":
          classes.push("bg-green-100", "border-green-300");
          break;
        case "incorrect":
          classes.push("bg-red-100", "border-red-300");
          break;
        case "neutral":
        default:
          // No additional styling for neutral state
          break;
      }

      return classes;
    },
  };

  // Computed properties for reactive state
  const incorrectCells = computed(() => getCellsWithState("incorrect"));
  const correctCells = computed(() => getCellsWithState("correct"));
  const totalIncorrect = computed(() => incorrectCells.value.length);
  const totalCorrect = computed(() => correctCells.value.length);

  return {
    inputBehavior,
    renderBehavior,

    // State management
    setIncorrect,
    setCorrect,
    setNeutral,
    setMultipleIncorrect,
    setMultipleCorrect,
    clearAll,
    clearCell,
    getCellValidationState,

    // Computed state
    incorrectCells: readonly(incorrectCells),
    correctCells: readonly(correctCells),
    totalIncorrect: readonly(totalIncorrect),
    totalCorrect: readonly(totalCorrect),

    // Control
    setEnabled,

    // Utilities
    getCellsWithState,
    isPrefilled,
  };
}

/**
 * Convenience function to register Sudoku validation behavior
 */
export function withSudokuValidationBehavior(controller: PuzzleController, bridge: any) {
  const behavior = useSudokuValidationHighlighter(controller);
  bridge.addInputBehaviour(() => behavior.inputBehavior);
  bridge.addRenderBehaviour(() => behavior.renderBehavior);
  return behavior;
}
