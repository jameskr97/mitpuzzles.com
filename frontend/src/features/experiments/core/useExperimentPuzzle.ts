// frontend/src/features/experiments/core/useExperimentPuzzle.ts

import { computed, ref } from "vue";
import { useExperimentPoints } from "./useExperimentPoints";
import { EngineSudoku } from "@/services/game/engines/games/sudoku";
import type { PuzzleController, PuzzleDefinition, PuzzleState, PuzzleUIState } from "@/services/game/engines/types";
import type { Cell } from "@/features/games.components/board.interaction";
import { useGameHistoryStore } from "@/store/useGameHistoryStore.ts";
import type { useExperimentContext } from "@/features/experiments/core/useExperimentContext.ts";

interface ExperimentPuzzleController extends PuzzleController {
  current_points: number;
  step_id: string;
  calculateCurrentPoints: () => number;
  recordPoints: () => number;
  get_incorrect_cells: () => { row: number; col: number }[];
  get_correct_cells: () => { row: number; col: number }[];
}

export function useExperimentPuzzle(
  step_id: string,
  definition: PuzzleDefinition,
  context: ReturnType<typeof useExperimentContext>,
): ExperimentPuzzleController {
  const historyStore = useGameHistoryStore();
  const pointsManager = useExperimentPoints();

  // Create sudoku engine with the specific definition
  const currentEngine = ref(new EngineSudoku(definition));
  const current_points = ref(0);

  // UI State - minimal for experiments
  const state_ui = ref<PuzzleUIState>({
    tutorial_mode: false,
    show_solved_state: false,
    show_violations: false,
  });

  // Computed puzzle state - same pattern as useFreeplayPuzzle
  const state_puzzle = computed<PuzzleState>(() => {
    return {
      definition: currentEngine.value.definition,
      board: currentEngine.value.board_state,
      solved: false,
      immutable_cells: currentEngine.value.immutable_cells,
      violations: [],
    };
  });

  // Handle cell clicks
  function handle_cell_click(cell: Cell, event: MouseEvent, override?: number) {
    // Record state before move
    const old_state = currentEngine.value.board_state[cell.row][cell.col];
    const old_board = JSON.parse(JSON.stringify(currentEngine.value.board_state));

    // Execute the move
    const success = currentEngine.value.handle_input_event("cell", "click", cell, event, override);

    // Record the move in history store
    if (success) {
      const new_state = currentEngine.value.board_state[cell.row][cell.col];
      const new_board = JSON.parse(JSON.stringify(currentEngine.value.board_state));

      const edata = context.getExperimentData();
      console.log(edata);

      historyStore.addExperimentEvent(edata.experimentId, tdata?.trialId, "sudoku", {
        action: "click",
        cell: { row: cell.row, col: cell.col },
        old_state,
        new_state,
        timestamp: Date.now(),
        before_action: old_board,
        after_action: new_board,
      });
    }
  }

  // Handle key presses
  function handle_cell_key_down(cell: Cell, event: KeyboardEvent) {
    // Record state before move
    const old_state = currentEngine.value.board_state[cell.row][cell.col];
    const old_board = JSON.parse(JSON.stringify(currentEngine.value.board_state));

    // Execute the moves
    const success = currentEngine.value.handle_input_event("cell", "keydown", cell, event);

    // Record the move in history store
    if (success) {
      const new_state = currentEngine.value.board_state[cell.row][cell.col];
      const new_board = JSON.parse(JSON.stringify(currentEngine.value.board_state));
      const edata = context.getExperimentData();
      const tdata = context.getCurrentTrialInfo();
      console.log(tdata);
      historyStore.addExperimentEvent(edata.experimentId, tdata?.trialId, "sudoku", {
        action: "keypress",
        cell: { row: cell.row, col: cell.col },
        old_state,
        new_state,
        timestamp: Date.now(),
        before_action: old_board,
        after_action: new_board,
      });
    }
  }

  // Calculate points based on current board state
  function calculateCurrentPoints(): number {
    const currentBoard = currentEngine.value.board_state;
    return pointsManager.recordStepPoints(step_id, currentBoard, definition);
  }

  // Record final points for this step
  function recordPoints(): number {
    return calculateCurrentPoints();
  }

  function getIncorrectCells(): { row: number; col: number }[] {
    // compare against solution hash (it's not actually a hash, but just the solution in plaintext)
    const incorrectCells: { row: number; col: number }[] = [];
    const solution = currentEngine.value.definition.solution_hash.split("").map(Number);
    const board = currentEngine.value.board_state;
    for (let row = 0; row < board.length; row++) {
      for (let col = 0; col < board[row].length; col++) {
        if (currentEngine.value.definition.initial_state[row][col] !== -1) continue;

        if (board[row][col] !== solution[row * currentEngine.value.definition.cols + col]) {
          incorrectCells.push({ row, col });
        }
      }
    }

    return incorrectCells;
  }

  function getCorrectCells(): { row: number; col: number }[] {
    const correctCells: { row: number; col: number }[] = [];
    const solution = currentEngine.value.definition.solution_hash.split("").map(Number);
    const board = currentEngine.value.board_state;
    for (let row = 0; row < board.length; row++) {
      for (let col = 0; col < board[row].length; col++) {
        if (currentEngine.value.definition.initial_state[row][col] !== -1) continue;

        if (board[row][col] === solution[row * currentEngine.value.definition.cols + col]) {
          correctCells.push({ row, col });
        }
      }
    }

    return correctCells;
  }

  function request_new_puzzle() {}

  function clear_puzzle() {}

  function check_solution() {}

  return {
    // Required PuzzleController interface
    state_puzzle,
    state_ui,
    handle_cell_click,
    handle_cell_key_down,
    request_new_puzzle,
    clear_puzzle,
    check_solution,
    get_incorrect_cells: getIncorrectCells,
    get_correct_cells: getCorrectCells,

    // Experiment-specific properties
    current_points: current_points.value,
    step_id,

    // Experiment-specific methods
    calculateCurrentPoints,
    recordPoints,
  };
}
