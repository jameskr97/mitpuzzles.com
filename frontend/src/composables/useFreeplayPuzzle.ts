import { PuzzleEngine } from "@/services/game/engines/PuzzleEngine.ts";
import { computed, nextTick, ref } from "vue";
import type { Cell } from "@/features/games.components/board.interaction.ts";
import type { PuzzleController, PuzzleDefinition, PuzzleState, PuzzleUIState } from "@/services/game/engines/types.ts";
import { EngineKakurasu } from "@/services/game/engines/games/kakurasu.ts";
import { EngineSudoku } from "@/services/game/engines/games/sudoku.ts";
import { EngineTents } from "@/services/game/engines/games/tents.ts";
import { EngineLightup } from "@/services/game/engines/games/lightup.ts";
import { EngineMinesweeper } from "@/services/game/engines/games/minesweeper.ts";
import { PuzzleConverter } from "@/services/game/engines/translator.ts";
import { useGameStateStore } from "@/store/useGameStateStore.ts";
import { useGameMetadataStore } from "@/store/useGameMetadataStore.ts";
import { useGameAttemptStore } from "@/store/useGameAttemptStore.ts";
import { useGameHistoryStore } from "@/store/useGameHistoryStore.ts";
import { useFreeplayLeaderboardStore } from "@/store/useFreeplayLeaderboardStore.ts";

// Factory function to create the right engine type
async function createEngine<T>(puzzle_type: string, definition: PuzzleDefinition<T>): Promise<PuzzleEngine> {
  const stateStore = useGameStateStore();
  const board = await stateStore.loadPuzzleState(puzzle_type);

  switch (puzzle_type) {
    case "sudoku":
      return new EngineSudoku(definition, board);
    case "kakurasu":
      return new EngineKakurasu(definition, board);
    case "tents":
      return new EngineTents(definition, board);
    case "lightup":
      return new EngineLightup(definition, board);
    case "minesweeper":
      return new EngineMinesweeper(definition, board);
    default:
      return new PuzzleEngine(definition, board);
  }
}

export async function useFreeplayPuzzle(puzzle_type: string): Promise<PuzzleController> {
  const metadataStore = useGameMetadataStore();
  const gameStore = useGameStateStore();
  const attemptStore = useGameAttemptStore();
  const historyStore = useGameHistoryStore();
  const leaderStore = useFreeplayLeaderboardStore();

  // get initial puzzle definition from defaults if available
  const default_difficulty = metadataStore.getSelectedVariant(puzzle_type);
  const puzzle = await gameStore.getOrFetchPuzzle(puzzle_type, default_difficulty[0], default_difficulty[1]);

  // UI State
  const show_solved_state_timeout = ref<ReturnType<typeof setTimeout>>();
  const state_ui = ref<PuzzleUIState>({
    tutorial_mode: false,
    show_solved_state: attemptStore.isPuzzleSolved(puzzle_type) ? true : false,
    show_violations: true,
    animate_success: false,
    animate_failure: false,
  });

  const state_puzzle = computed<PuzzleState>(() => {
    return {
      definition: currentEngine.value.definition,
      board: currentEngine.value.board_state,
      solved: attemptStore.isPuzzleSolved(puzzle_type),
      immutable_cells: currentEngine.value.immutable_cells,
      violations: state_ui.value.tutorial_mode ? currentEngine.value.get_violations() : [],
    };
  });

  // Local state
  const currentEngine = ref<PuzzleEngine<any>>(await createEngine(puzzle_type, puzzle));
  const save_board_state = () =>
    gameStore.updatePuzzleState(puzzle_type, currentEngine.value.board_state).catch((error) => {
      console.warn("Failed to save puzzle state:", error);
    });

  // Actions
  async function load_new_puzzle() {
    state_ui.value.show_solved_state = false;
    gameStore.clearPuzzleState(puzzle_type);
    await historyStore.clearEvents(puzzle_type, "freeplay");

    const variant = metadataStore.getSelectedVariant(puzzle_type);
    const definition = await gameStore.requestNewPuzzle(puzzle_type, variant[0], variant[1]);
    currentEngine.value = await createEngine(puzzle_type, definition);
    attemptStore.resetPuzzleProgress(puzzle_type);
    attemptStore.startTimer(puzzle_type);
    save_board_state();
  }

  function handle_cell_click(cell: Cell, event: MouseEvent, override?: number) {
    // recording
    const old_state = currentEngine.value.board_state[cell.row][cell.col];
    const old_board = JSON.parse(JSON.stringify(currentEngine.value.board_state));

    // do the action
    const success = currentEngine.value.handle_input_event("cell", "click", cell, event, override);

    // recording
    if (success) {
      const new_state = currentEngine.value.board_state[cell.row][cell.col];
      const new_board = JSON.parse(JSON.stringify(currentEngine.value.board_state));
      historyStore.addEvent(puzzle_type, "freeplay", {
        action: "click",
        cell: { row: cell.row, col: cell.col },
        old_state,
        new_state,
        timestamp: Date.now(),
        before_action: PuzzleConverter.toResearch(old_board, puzzle_type),
        after_action: PuzzleConverter.toResearch(new_board, puzzle_type),
      });
      save_board_state();
    }
  }

  function handle_cell_key_down(cell: Cell, event: KeyboardEvent) {
    currentEngine.value.handle_input_event("cell", "keydown", cell, event);
    save_board_state();
  }

  function clear_puzzle() {
    const old_board = JSON.parse(JSON.stringify(currentEngine.value.board_state));
    currentEngine.value.board_clear();
    const new_board = JSON.parse(JSON.stringify(currentEngine.value.board_state));
    state_ui.value.show_solved_state = false;
    historyStore.addEvent(puzzle_type, "freeplay", {
      action: "clear",
      timestamp: Date.now(),
      before_action: old_board,
      after_action: new_board,
    });
    save_board_state();
  }

  async function check_solution() {
    clearTimeout(show_solved_state_timeout.value)
    await nextTick();
    const res = await currentEngine.value.check_solution();
    state_ui.value.show_solved_state = true;
    state_ui.value.animate_success = res;
    state_ui.value.animate_failure = !res;

    if (res) {
      attemptStore.stopTimer(puzzle_type);
      await attemptStore.markPuzzleSolved(puzzle_type);
      await historyStore.uploadAttemptHistory(state_puzzle.value.definition, "freeplay");

      const [size, difficulty] = metadataStore.getSelectedVariant(puzzle_type);
      await leaderStore.refreshLeaderboard(puzzle_type, size, difficulty);
    } else {
      show_solved_state_timeout.value = setTimeout(() => (state_ui.value.show_solved_state = false), 3000);
    }

    setTimeout(() => {
      state_ui.value.animate_failure = false;
      state_ui.value.animate_success = false;
    }, 100);
  }

  return {
    // State
    state_puzzle,
    state_ui,

    // Actions
    request_new_puzzle: load_new_puzzle,
    handle_cell_click,
    handle_cell_key_down,
    clear_puzzle,
    check_solution,
  };
}
