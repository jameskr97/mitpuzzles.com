import { useLocalStorage } from "@vueuse/core";
import type { AnyPuzzleState, MutablePuzzleState } from "@/services/states.ts";
import { emit, on } from "@/services/eventbus.ts";
import type { WebSocketMessage } from "@/services/eventbus.modules/websocket.ts";
import type { Cell } from "@/features/games.components/board.interaction.ts";
import { useActivePuzzleStore } from "@/store/useActivePuzzleStore.ts";
import { useCurrentExperiment } from "@/store/useCurrentExperiment.ts";
import { computed } from "vue";
import { getPuzzleSession, useCurrentPuzzle } from "@/composables/useCurrentPuzzle.ts";

function mapButtonToName(button: number): "left" | "right" | "middle" | "unknown" {
  // prettier-ignore
  switch (button) {
    case 0:
      return "left";
    case 1:
      return "middle";
    case 2:
      return "right";
    default:
      return "unknown";
  }
}

export interface GameModuleInterface {
  // Business actions (emit websocket commands)
  resumePuzzle(puzzleType: string): void;

  handle_cell_click(cell: Cell, button: number, state_override?: number): void;

  clear_puzzle_state(): void;

  clear_solved_state(): void;

  get_solved_state(): boolean;

  toggle_tutorial(enabled: boolean): void;

  request_new_puzzle(puzzle_size: string | undefined, puzzle_difficulty: string | undefined): void;

  request_submit(): void;

  // Local reactive state queries
  getSessionID(puzzleType: string): string | undefined;

  getPuzzleState(sessionId: string): MutablePuzzleState | undefined;

  _cleanup(): void;
}

export const gameModule = {
  name: "game",
  setup(): GameModuleInterface {
    ////////////////////////////////////////////////////////////////////////
    // State Management
    const store = useActivePuzzleStore();
    const experimentStore = useCurrentExperiment();
    const isProlific = computed(() => experimentStore.prolific_session_id !== null);
    const session_lookup = useLocalStorage<Record<string, string>>("mitlogic.puzzles:active_session_ids", {});
    let activePuzzleType: string | null = null;

    ////////////////////////////////////////////////////////////////////////
    // Helpers
    const getActiveSessionID = () => {
      if (!activePuzzleType) return null;
      return session_lookup.value[activePuzzleType] || null;
    };

    function send_command<T>(command: string, data: T, session_id?: string) {
      const message: WebSocketMessage<T> = { type: command, data };
      if (session_id) message.session_id = session_id;
      emit("socket:send", message);
    }

    ////////////////////////////////////////////////////////////////////////
    // WebSocket Message Handling
    const unsub_funcs: Array<CallableFunction> = [];

    ////////////////////////////////////////////////////////////////////////
    // Event Handler Functions
    function on_game_state(session_id: string, state: AnyPuzzleState) {
      if (session_id && state.puzzle_type) {
        store.setPuzzleState(state.puzzle_type, session_id, state);
        if (state.is_solved) {
          store.setPuzzleSolved(session_id, state.is_solved);
        }
      }
    }

    unsub_funcs.push(
      on("game:state", (event: WebSocketMessage<AnyPuzzleState>) => on_game_state(event.data.session_id, event.data)),
    );
    unsub_funcs.push(on("game:set_active_puzzle", (x) => (activePuzzleType = x)));
    unsub_funcs.push(
      on("game:submit_result", (event: WebSocketMessage<boolean>) => {
        const session_id = getActiveSessionID();
        if (!session_id) return;
        store.setPuzzleSolved(session_id, event.data);
      }),
    );

    return {
      resumePuzzle(puzzle_type: string) {
        if (isProlific.value) {
          send_command("prolific:resume", {});
          return;
        }

        const session_id = store.getSessionID(puzzle_type);
        if (session_id) {
          send_command("cmd:resume", { puzzle_type }, session_id); // Try to resume existing session
        } else {
          send_command("cmd:create", { puzzle_type }); // Create new session if none exists
        }
      },
      getPuzzleState(session_id: string): MutablePuzzleState | undefined {
        return store.getState(session_id);
      },
      getSessionID(puzzleType: string): string | undefined {
        return session_lookup.value[puzzleType] ?? null;
      },
      clear_solved_state() {
        const session_id = getActiveSessionID();
        if (session_id) {
          store.clearSolvedState(session_id);
        }
      },
      clear_puzzle_state() {
        const sid = getActiveSessionID();
        if (!sid) return;
        send_command("cmd:reset", {}, sid);
      },
      get_solved_state(): boolean {
        const sid = getActiveSessionID();
        if (!sid) return false;
        return store.isPuzzleSolved(sid);
      },
      handle_cell_click(cell: Cell, button: number = 0, state_override?: number) {
        const sid = getActiveSessionID();
        if (!sid) return;
        store.clearSolvedState(sid);
        let payload: ActionPayload = {
          target: "cell",
          action: "click",
          position: { zone: cell.zone, row: cell.row, col: cell.col, button: mapButtonToName(button) },
        };
        if (state_override !== undefined) {
          payload.position.state = state_override;
        }

        send_command("cmd:action", payload, sid);
      },

      toggle_tutorial(enabled: boolean) {
        const sid = getActiveSessionID();
        if (!sid) return;
        send_command("cmd:toggle_tutorial", { enabled }, sid);
      },

      request_new_puzzle(puzzle_size: string | undefined, puzzle_difficulty: string | undefined) {
        const sid = getActiveSessionID();
        if (!sid) return;
        let payload = {
          puzzle_type: activePuzzleType,
          puzzle_size: puzzle_size,
          puzzle_difficulty: puzzle_difficulty,
        };
        store.clearSolvedState(sid);
        send_command("cmd:create", payload);
      },
      request_submit() {
        const sid = getActiveSessionID();
        if (!sid) return;
        if (!activePuzzleType) return;
        const currentPuzzle = getPuzzleSession(activePuzzleType);
        send_command("cmd:submit", {duration: currentPuzzle?.timer.get_duration_ms()}, sid);
      },

      _cleanup() {
        unsub_funcs.forEach((func) => func());
      },
    };
  },
};
