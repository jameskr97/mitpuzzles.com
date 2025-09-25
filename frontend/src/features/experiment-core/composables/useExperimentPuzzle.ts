import { computed, nextTick, ref, type Ref } from "vue";
import type { PuzzleController, PuzzleDefinition, PuzzleState, PuzzleUIState } from "@/services/game/engines/types";
import type { Cell } from "@/features/games.components/board.interaction";
import { createPuzzleEngine } from "@/utils";
import type { GraphExecutor } from "@/features/experiment-core/graph/GraphExecutor";
import { PuzzleConverter } from "@/services/game/engines/translator.ts";

/**
 * experiment-core puzzle composable with integrated data collection
 * bridges between puzzle engines and experiment data collection
 */
export function useExperimentPuzzle(puzzle_def: Ref<PuzzleDefinition>, executor: Ref<GraphExecutor>): PuzzleController {
  const engine = ref(createPuzzleEngine(puzzle_def.value));

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
      definition: engine.value.definition,
      board: engine.value.board_state,
      solved: false, // managed by trial component
      immutable_cells: engine.value.immutable_cells,
      violations: [], // not showing violations in experiments
    };
  });

  // handle cell interactions with data recording
  function handle_cell_click(cell: Cell, event: MouseEvent, override?: number) {
    const old_value = engine.value.board_state[cell.row!][cell.col!];
    const old_board = JSON.parse(JSON.stringify(engine.value.board_state));
    const success = engine.value.handle_input_event("cell", "click", cell, event, override);
    if (!success) return;
    const new_value = engine.value.board_state[cell.row!][cell.col!];
    const new_board = JSON.parse(JSON.stringify(engine.value.board_state));

    // record interaction in experiment data collection
    executor.value.data_collection.record_interaction(
      "cell_click",
      node_id.value,
      {
        cell: { row: cell.row, col: cell.col },
        old_value,
        new_value,
        old_board,
        new_board,
        timestamp: Date.now(),
      },
      executor.value.current_trial_id!,
    );
  }

  function handle_cell_key_down(cell: Cell, event: KeyboardEvent) {
    const old_value = engine.value.board_state[cell.row!][cell.col!];
    const old_board = JSON.parse(JSON.stringify(engine.value.board_state));
    const success = engine.value.handle_input_event("cell", "keydown", cell, event);
    if (!success) return;

    const new_value = engine.value.board_state[cell.row!][cell.col!];
    const new_board = JSON.parse(JSON.stringify(engine.value.board_state));

    // record interaction in experiment data collection
    executor.value.data_collection.record_interaction(
      "cell_keypress",
      node_id.value,
      {
        cell: { row: cell.row, col: cell.col },
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

  // NOTE(james): this just informs the data recorder that we've focused on a cell.
  //              no game-engine is informed about focus events.
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

  // get incorrect cells compared to solution
  function get_incorrect_cells(): { row: number; col: number }[] {
    const incorrect_cells: { row: number; col: number }[] = [];
    const solution = PuzzleConverter.fromResearch(
      engine.value.definition.solution!,
      engine.value.definition.puzzle_type,
    );
    const board = JSON.parse(JSON.stringify(engine.value.board_state));

    for (let row = 0; row < board.length; row++) {
      for (let col = 0; col < board[row].length; col++) {
        if (engine.value.definition.initial_state[row][col] !== -1) continue; // skip prefilled cells

        if (board[row][col] !== solution[row][col]) {
          incorrect_cells.push({ row, col });
        }
      }
    }
    return incorrect_cells;
  }

  // get correct cells compared to solution
  function get_correct_cells(): { row: number; col: number }[] {
    const correct_cells: { row: number; col: number }[] = [];
    const solution = PuzzleConverter.fromResearch(
      engine.value.definition.solution!,
      engine.value.definition.puzzle_type,
    );
    const board = JSON.parse(JSON.stringify(engine.value.board_state));

    for (let row = 0; row < board.length; row++) {
      for (let col = 0; col < board[row].length; col++) {
        if (engine.value.definition.initial_state[row][col] !== -1) continue; // skip prefilled cells

        if (board[row][col] === solution[row][col]) {
          correct_cells.push({ row, col });
        }
      }
    }
    return correct_cells;
  }

  async function check_solution(): Promise<boolean> {
    clearTimeout(show_solved_state_timeout.value);
    await nextTick();
    const is_solved = await engine.value.check_solution();
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
    state_ui, // kept for API compatibility
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
