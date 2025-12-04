import { computed, nextTick, ref, type Ref } from "vue";
import type { PuzzleController, PuzzleDefinition, PuzzleState, PuzzleUIState, Cell } from "@/core/games/types/puzzle-types.ts";
import type { GraphExecutor } from "@/features/experiment-core/graph/GraphExecutor";
import { useStateCycler, useSolutionChecker } from "@/core/games/composables";

/**
 * Cycle states for each puzzle type (research format values)
 */
const CYCLE_STATES: Record<string, number[]> = {
  minesweeper: [-1, -3, -4], // UNMARKED → FLAG → SAFE
  kakurasu: [-1, 1, 0],      // EMPTY → BLACK → CROSS
  nonograms: [-1, 1, 0],     // EMPTY → BLACK → CROSS
  tents: [-1, -3, -4],       // EMPTY → TENT → GREEN
  lightup: [-1, -3, -4],     // EMPTY → BULB → CROSS
  mosaic: [-1, -3, -4],      // UNMARKED → SHADED → CROSS
  aquarium: [-1, -3, -4],    // EMPTY → WATER → CROSS
  norinori: [-1, -3, -4],    // EMPTY → SHADED → CROSS
};

/**
 * Positive values for solution checking (research format)
 */
const POSITIVE_VALUES: Record<string, number[]> = {
  minesweeper: [-3],         // FLAG
  kakurasu: [1],             // BLACK
  nonograms: [1],            // BLACK
  tents: [-3],               // TENT
  lightup: [-3],             // BULB
  mosaic: [-3],              // SHADED
  sudoku: [1, 2, 3, 4, 5, 6, 7, 8, 9],
  aquarium: [-3],            // WATER
  norinori: [-3],            // SHADED
};

/**
 * experiment-core puzzle composable with integrated data collection
 * Uses research format directly - no conversion needed
 */
export function useExperimentPuzzle(puzzle_def: Ref<PuzzleDefinition>, executor: Ref<GraphExecutor>): PuzzleController {
  const puzzle_type = puzzle_def.value.puzzle_type;

  // Direct state management - clone initial state
  const board = ref<number[][]>(
    puzzle_def.value.initial_state.map(row => [...row])
  );

  // Compute immutable cells from initial state (prefilled cells are immutable)
  const immutable_cells = computed(() =>
    puzzle_def.value.initial_state.map(row =>
      row.map(cell => (cell !== -1 ? 1 : 0))
    )
  );

  // State cycler for click behavior
  const cycle_states = CYCLE_STATES[puzzle_type] || [-1, -3, -4];
  const { cycle_state } = useStateCycler(cycle_states);

  // Solution checker
  const positive_values = POSITIVE_VALUES[puzzle_type] || [-3];
  const solution_checker = useSolutionChecker({
    type: "cell-grid",
    solution_hash: puzzle_def.value.solution_hash,
    expected_solution: puzzle_def.value.solution,
    positive_values,
  });

  // get node_id from executor with proper error handling
  const node_id = computed(() => {
    const current_node = executor.value.current_node;
    if (!current_node?.id) return "unknown-node";
    return current_node.id;
  });

  // state_ui for API compatibility
  const recorded_solution = ref(false);
  const show_solved_state_timeout = ref<ReturnType<typeof setTimeout>>();
  const state_ui = ref<PuzzleUIState>({
    tutorial_mode: false,
    show_solved_state: false,
    show_violations: false,
    animate_success: false,
    animate_failure: false,
  });

  // reactive puzzle state for display
  const state_puzzle = computed<PuzzleState>(() => {
    return {
      definition: puzzle_def.value,
      board: board.value,
      solved: false, // managed by trial component
      immutable_cells: immutable_cells.value,
      violations: [], // not showing violations in experiments
    };
  });

  /**
   * Check if a cell is editable (not prefilled)
   */
  function is_cell_editable(row: number, col: number): boolean {
    return puzzle_def.value.initial_state[row][col] === -1;
  }

  /**
   * Handle cell click with data recording
   */
  function handle_cell_click(cell: Cell, event: MouseEvent, override?: number) {
    const row = cell.row!;
    const col = cell.col!;

    if (!is_cell_editable(row, col)) return;

    const old_value = board.value[row][col];
    const old_board = JSON.parse(JSON.stringify(board.value));

    // Calculate new value
    let new_value: number;
    if (override !== undefined) {
      new_value = override;
    } else {
      new_value = cycle_state(old_value, event.button);
    }

    // Update board
    board.value[row][col] = new_value;
    const new_board = JSON.parse(JSON.stringify(board.value));

    // record interaction in experiment data collection
    executor.value.data_collection.record_interaction(
      "cell_click",
      node_id.value,
      {
        cell: { row, col },
        old_value,
        new_value,
        old_board,
        new_board,
        timestamp: Date.now(),
      },
      executor.value.current_trial_id!,
    );
  }

  /**
   * Handle keyboard input (for sudoku-like games)
   */
  function handle_cell_key_down(cell: Cell, event: KeyboardEvent) {
    const row = cell.row!;
    const col = cell.col!;

    if (!is_cell_editable(row, col)) return;

    const old_value = board.value[row][col];
    const old_board = JSON.parse(JSON.stringify(board.value));

    // Handle keyboard input
    let new_value: number;
    const key = event.key;

    if (key === "Backspace" || key === "Delete" || key === "0") {
      new_value = -1; // EMPTY in research format
    } else {
      const num = parseInt(key);
      if (isNaN(num) || num < 1 || num > 9) return;
      new_value = num;
    }

    if (old_value === new_value) return;

    // Update board
    board.value[row][col] = new_value;
    const new_board = JSON.parse(JSON.stringify(board.value));

    // record interaction in experiment data collection
    executor.value.data_collection.record_interaction(
      "cell_keypress",
      node_id.value,
      {
        cell: { row, col },
        key: event.key,
        old_value,
        new_value,
        old_board,
        new_board,
        timestamp: Date.now(),
      },
      executor.value.current_trial_id!,
    );
  }

  /**
   * Handle cell focus (just records, no state change)
   */
  function handle_cell_focus(cell: Cell, _event: MouseEvent) {
    executor.value.data_collection.record_interaction(
      "cell_focus",
      node_id.value,
      {
        cell: { row: cell.row, col: cell.col },
        timestamp: Date.now(),
      },
      executor.value.current_trial_id!,
    );
  }

  /**
   * Get incorrect cells compared to solution
   * Both board and solution are in research format - direct comparison
   */
  function get_incorrect_cells(): { row: number; col: number }[] {
    const incorrect_cells: { row: number; col: number }[] = [];
    const solution = puzzle_def.value.solution!;

    for (let row = 0; row < board.value.length; row++) {
      for (let col = 0; col < board.value[row].length; col++) {
        // skip prefilled cells
        if (puzzle_def.value.initial_state[row][col] !== -1) continue;

        if (board.value[row][col] !== solution[row][col]) {
          incorrect_cells.push({ row, col });
        }
      }
    }
    return incorrect_cells;
  }

  /**
   * Get correct cells compared to solution
   * Both board and solution are in research format - direct comparison
   */
  function get_correct_cells(): { row: number; col: number }[] {
    const correct_cells: { row: number; col: number }[] = [];
    const solution = puzzle_def.value.solution!;

    for (let row = 0; row < board.value.length; row++) {
      for (let col = 0; col < board.value[row].length; col++) {
        // skip prefilled cells
        if (puzzle_def.value.initial_state[row][col] !== -1) continue;

        if (board.value[row][col] === solution[row][col]) {
          correct_cells.push({ row, col });
        }
      }
    }
    return correct_cells;
  }

  /**
   * Check if puzzle is solved
   */
  async function check_solution(): Promise<boolean> {
    clearTimeout(show_solved_state_timeout.value);
    await nextTick();

    const is_solved = await solution_checker.check(board.value);

    state_ui.value.show_solved_state = true;
    state_ui.value.animate_success = is_solved;
    state_ui.value.animate_failure = !is_solved;

    if (!recorded_solution.value) {
      executor.value.data_collection.record_interaction(
        "attempt_solve",
        node_id.value,
        { correct: is_solved },
        executor.value.current_trial_id!,
      );
      recorded_solution.value = true;
    }

    setTimeout(() => {
      state_ui.value.animate_failure = false;
      state_ui.value.animate_success = false;
    }, 100);

    return is_solved;
  }

  return {
    state_puzzle,
    state_ui,
    handle_cell_click,
    handle_cell_key_down,
    handle_cell_focus,
    get_incorrect_cells,
    get_correct_cells,
    check_solution,
    // no-op for compatibility
    request_new_puzzle: () => {},
    clear_puzzle: () => {},
  };
}
