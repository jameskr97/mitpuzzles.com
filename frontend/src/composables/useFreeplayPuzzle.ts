import { PuzzleEngine } from "@/services/game/engines/PuzzleEngine.ts";
import { computed, nextTick, ref } from "vue";
import type { Cell } from "@/features/games.components/board.interaction.ts";
import type { PuzzleController, PuzzleState, PuzzleUIState } from "@/services/game/engines/types.ts";
import { PuzzleConverter } from "@/services/game/engines/translator.ts";
import { usePuzzleDefinitionStore } from "@/store/puzzle/usePuzzleDefinitionStore.ts";
import { usePuzzleMetadataStore } from "@/store/puzzle/usePuzzleMetadataStore.ts";
import { usePuzzleLeaderboardStore } from "@/store/puzzle/usePuzzleLeaderboardStore.ts";
import { usePuzzleProgressStore } from "@/store/puzzle/usePuzzleProgressStore.ts";
import { useGameRecorder } from "@/composables/useGameRecorder.ts";
import { usePuzzleHistoryStore } from "@/store/puzzle/usePuzzleHistoryStore.ts";
import { createPuzzleEngine } from "@/utils.ts";
import { broadcast_channel_service } from "@/services/broadcast_channel";

export async function useFreeplayPuzzle(puzzle_type: string): Promise<PuzzleController> {
  const metadataStore = usePuzzleMetadataStore();
  const progressStore = usePuzzleProgressStore();
  const puzzleStore = usePuzzleDefinitionStore();
  const historyStore = usePuzzleHistoryStore();
  const leaderStore = usePuzzleLeaderboardStore();
  const recorder = useGameRecorder({
    capture_hover_events: true,
  })

  // get initial puzzle definition from defaults if available
  const selected = metadataStore.getSelectedVariant(puzzle_type);
  const puzzle_definition = await puzzleStore.getOrFetchPuzzle(puzzle_type, selected[0], selected[1]);

  // UI State
  const show_solved_state_timeout = ref<ReturnType<typeof setTimeout>>();
  const state_ui = ref<PuzzleUIState>({
    tutorial_mode: false,
    show_solved_state: progressStore.is_puzzle_solved(puzzle_type) ? true : false,
    show_violations: true,
    animate_success: false,
    animate_failure: false,
  });

  const state_puzzle = computed<PuzzleState>(() => {
    const violations = state_ui.value.tutorial_mode ? currentEngine.value.get_violations() : [];
    
    // Mark tutorial as used if tutorial mode is on AND violations are shown
    if (state_ui.value.tutorial_mode && violations.length > 0) {
      progressStore.mark_tutorial_used(puzzle_type);
    }
    
    return {
      definition: currentEngine.value.definition,
      board: currentEngine.value.board_state,
      solved: progressStore.is_puzzle_solved(puzzle_type),
      immutable_cells: currentEngine.value.immutable_cells,
      violations,
    };
  });

  // Local state
  const currentEngine = ref<PuzzleEngine<any>>(createPuzzleEngine(puzzle_definition, progressStore.current_puzzle_states[puzzle_type]));
  const save_board_state = () => progressStore.update_puzzle_state(puzzle_type, currentEngine.value.board_state).catch((error) => {
      console.warn("Failed to save puzzle state:", error);
    });

  // if this is first load, initialize progress
  if (!progressStore.timestamp_start[puzzle_type]) await progressStore.reset_puzzle(puzzle_type, currentEngine.value.initial_state)

  // setup broadcast listeners for cross-tab sync
  // listen for game state updates from other tabs
  const broadcast_unsubscribers: (() => void)[] = [];
  broadcast_unsubscribers.push(
    broadcast_channel_service.subscribe('game_state_update', (message) => {
      if (message.puzzle_type === puzzle_type) {
        console.log("Updating puzzle engine from broadcast", message);
        currentEngine.value.board_state = message.data.board_state;
      }
    })
  );

  // listen for game resets from other tabs
  broadcast_unsubscribers.push(
    broadcast_channel_service.subscribe('game_reset', (message) => {
      if (message.puzzle_type === puzzle_type) {
        console.log("Resetting puzzle engine from broadcast", message);
        currentEngine.value.board_state = message.data.initial_state;
        state_ui.value.show_solved_state = false;
      }
    })
  );

  // listen for puzzle solved from other tabs
  broadcast_unsubscribers.push(
    broadcast_channel_service.subscribe('game_solved', (message) => {
      if (message.puzzle_type === puzzle_type) {
        console.log("Marking puzzle solved from broadcast", message);
        state_ui.value.show_solved_state = true;
        state_ui.value.animate_success = true;
        setTimeout(() => {
          state_ui.value.animate_success = false;
        }, 100);
      }
    })
  );

  // listen for new puzzle from other tabs
  broadcast_unsubscribers.push(
    broadcast_channel_service.subscribe('new_puzzle', (message) => {
      if (message.puzzle_type === puzzle_type) {
        console.log("Loading new puzzle from broadcast", message);
        const definition = message.data.puzzle_definition;
        const transformed_board = PuzzleConverter.fromResearch(definition.initial_state, puzzle_type);
        
        // create new engine with the broadcasted puzzle definition
        currentEngine.value = createPuzzleEngine(definition, transformed_board);
        state_ui.value.show_solved_state = false;
      }
    })
  );

  // Actions
  async function load_new_puzzle() {
    state_ui.value.show_solved_state = false;

    const variant = metadataStore.getSelectedVariant(puzzle_type);
    const definition = await puzzleStore.requestNewPuzzle(puzzle_type, variant[0], variant[1]);
    const transformed_board = PuzzleConverter.fromResearch(definition.initial_state, puzzle_type);
    await progressStore.reset_puzzle(puzzle_type, transformed_board);
    await historyStore.clear_events(puzzle_type, "freeplay")

    currentEngine.value = createPuzzleEngine(definition, progressStore.current_puzzle_states[puzzle_type]);
    
    // broadcast new puzzle to other tabs
    broadcast_channel_service.broadcast_new_puzzle(puzzle_type, definition);
  }

  function handle_cell_click(cell: Cell, event: MouseEvent, override?: number) {
    const old_value = currentEngine.value.board_state[cell.row!][cell.col!];
    const success = currentEngine.value.handle_input_event("cell", "click", cell, event, override);
    if (!success) return;

    const new_value = currentEngine.value.board_state[cell.row!][cell.col!];
    recorder.record_click(puzzle_type, cell, old_value, new_value);
    save_board_state();
  }

  function handle_cell_key_down(cell: Cell, event: KeyboardEvent) {
    const old_value = currentEngine.value.board_state[cell.row!][cell.col!];
    const success = currentEngine.value.handle_input_event("cell", "keydown", cell, event);
    if (!success) return;

    const new_value = currentEngine.value.board_state[cell.row!][cell.col!];
    recorder.record_keypress(puzzle_type, event.key, cell, old_value, new_value);
    save_board_state();
  }

  function handle_hover_start(cell: Cell, _event: MouseEvent): void {
    // start tracking hover time for this cell
    recorder.startHoverTimer(puzzle_type, cell);
  }

  function handle_hover_end(cell: Cell, _event: MouseEvent): void {
    // end tracking hover time
    recorder.endHoverTimer(puzzle_type);
  }

  function clear_puzzle() {
    const old_board = JSON.parse(JSON.stringify(currentEngine.value.board_state));
    currentEngine.value.board_clear();
    const new_board = JSON.parse(JSON.stringify(currentEngine.value.board_state));
    recorder.record_clear(puzzle_type, old_board, new_board);
    state_ui.value.show_solved_state = false;
    progressStore.reset_gutter_markings(puzzle_type);
    save_board_state();
  }

  async function check_solution(): Promise<boolean> {
    clearTimeout(show_solved_state_timeout.value);
    await nextTick();
    const is_solved = await currentEngine.value.check_solution();
    state_ui.value.show_solved_state = true;
    state_ui.value.animate_success = is_solved;
    state_ui.value.animate_failure = !is_solved;

    if (is_solved) {
      await progressStore.mark_puzzle_solved(puzzle_type);
      const [size, difficulty] = metadataStore.getSelectedVariant(puzzle_type);
      await historyStore.upload_attempt_history(puzzle_type, "freeplay")
      await leaderStore.refreshLeaderboard(puzzle_type, size, difficulty);
    } else {
      show_solved_state_timeout.value = setTimeout(() => (state_ui.value.show_solved_state = false), 3000);
    }

    setTimeout(() => {
      state_ui.value.animate_failure = false;
      state_ui.value.animate_success = false;
    }, 100);

    return is_solved
  }

  return {
    // State
    state_puzzle,
    state_ui,

    // Actions
    request_new_puzzle: load_new_puzzle,
    handle_cell_click,
    handle_cell_key_down,
    handle_hover_start,
    handle_hover_end,
    clear_puzzle,
    check_solution,
  };
}
