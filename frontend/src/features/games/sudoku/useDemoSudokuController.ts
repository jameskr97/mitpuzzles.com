import { reactive, ref } from "vue";
import type { PuzzleController, PuzzleDefinition, PuzzleState } from "@/services/game/engines/types.ts";
import { createPuzzleInteractionBridge } from "@/features/games.composables/setupPuzzleInteractionBridge.ts";
import { withSudokuBehaviors } from "@/features/games/sudoku/useSudokuCellHighlighter.ts";
import { withSudokuFocusBehavior } from "@/features/games/sudoku/useSudokuFocusHighlighter.ts";

export interface DemoSudokuOptions {
  initial_board?: number[][];
  allow_prefilled_modification?: boolean;
  cycle_mode?: boolean; // true = click cycles through numbers, false = click sets to 1
}

export function useDemoSudokuController(puzzle_definition: Partial<PuzzleDefinition>, options: DemoSudokuOptions = {}) {
  const {
    initial_board = puzzle_definition.initial_state || [],
    allow_prefilled_modification = false,
    cycle_mode = true,
  } = options;

  // Create reactive state for the demo
  const demo_puzzle_state = reactive<PuzzleState>({
    definition: puzzle_definition as PuzzleDefinition,
    board: JSON.parse(JSON.stringify(initial_board)), // Deep copy
    solved: false,
    immutable_cells: puzzle_definition.initial_state || [],
    violations: [],
  });

  // Create minimal controller
  const demo_controller: PuzzleController = {
    state_puzzle: ref(demo_puzzle_state),
    state_ui: ref({
      tutorial_mode: false,
      show_solved_state: false,
      show_violations: false,
    }),

    handle_cell_click: (cell, event) => {
      const current_value = demo_puzzle_state.board[cell.row][cell.col];
      const is_prefilled = demo_puzzle_state.definition.initial_state[cell.row][cell.col] !== 0;

      if (is_prefilled && !allow_prefilled_modification) return;

      if (cycle_mode) {
        // Cycle through numbers 1-9, then back to 0 (empty)
        const next_value = current_value >= 9 ? 0 : current_value + 1;
        demo_puzzle_state.board[cell.row][cell.col] = next_value;
      } else {
        // Simple toggle: empty -> 1, anything else -> empty
        demo_puzzle_state.board[cell.row][cell.col] = current_value === 0 ? 1 : 0;
      }
    },

    handle_cell_key_down: (cell, event, key) => {
      const is_prefilled = demo_puzzle_state.definition.initial_state[cell.row][cell.col] !== 0;

      if (is_prefilled && !allow_prefilled_modification) return;

      // Handle number input (1-9) or clear (0, Delete, Backspace)
      const keyAsNumber = Number(key);
      if (typeof keyAsNumber === "number" && keyAsNumber >= 1 && keyAsNumber <= 9) {
        demo_puzzle_state.board[cell.row][cell.col] = keyAsNumber;
      } else if (key === "0" || key === "Delete" || key === "Backspace") {
        demo_puzzle_state.board[cell.row][cell.col] = 0;
      }
    },

    request_new_puzzle: () => {
      // Reset to initial state
      demo_puzzle_state.board = JSON.parse(JSON.stringify(initial_board));
    },

    clear_puzzle: () => {
      // Clear all non-prefilled cells
      demo_puzzle_state.board.forEach((row, r) => {
        row.forEach((cell, c) => {
          const is_prefilled = demo_puzzle_state.definition.initial_state[r][c] !== 0;
          if (!is_prefilled) {
            demo_puzzle_state.board[r][c] = 0;
          }
        });
      });
    },

    check_solution: () => {
      // Basic completion check (could be enhanced)
      const is_complete = demo_puzzle_state.board.every((row) => row.every((cell) => cell !== 0));
      demo_puzzle_state.solved = is_complete;
    },
  };

  // Create interaction bridge
  const demo_bridge = createPuzzleInteractionBridge(demo_controller);
  withSudokuBehaviors(demo_controller, demo_bridge);
  withSudokuFocusBehavior(demo_controller, demo_bridge);

  return {
    puzzle_state: demo_puzzle_state,
    controller: demo_controller,
    interact: demo_bridge,
    // Utility methods
    reset: () => demo_controller.request_new_puzzle(),
    clear: () => demo_controller.clear_puzzle(),
    check: () => demo_controller.check_solution(),
  };
}
