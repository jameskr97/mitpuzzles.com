import { useLocalStorage, useWebSocket } from "@vueuse/core";
import { ref, computed, reactive, watch } from "vue";
import type { AnyPuzzleState, MutablePuzzleState } from "@/services/states.ts";
import { defineStore } from "pinia";
import type { Cell } from "@/features/games.components/board.interaction.ts";

////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////
//////// Protocol message types
interface WebSocketMessage<T = any> {
  type: string;
  data: T;
  session_id?: string;
  actor_id?: string;
}

export interface ActionPosition {
  row: number;
  col: number;
  zone: "game" | "topGutter" | "leftGutter" | "rightGutter" | "bottomGutter";
  button?: "left" | "right" | "middle" | "unknown";
  state?: number;
  direction?: "top" | "right" | "bottom" | "left";
  key?: string;
}

export interface ActionPayload {
  target: "cell" | "row" | "column" | "border";
  action: string; // 'click', 'rightclick', 'mousedown', 'mouseup', 'keydown', 'keyup', etc.
  position: ActionPosition;
}

interface SubmitResult {
  is_solved: boolean;
}

interface UserCountResult {
  user_count: number;
}

export const useActivePuzzleStore = defineStore("puzzle_session", () => {
  // user game sessions
  const puzzle_states = ref<Record<string, MutablePuzzleState>>({});
  const session_lookup = useLocalStorage<Record<string, string>>("mitlogic.puzzles:active_session_ids", {});
  const puzzle_solved = ref<Record<string, boolean>>({});
  // admin monitoring view
  const monitor_user_count = ref(0);
  const monitored_users_games = ref<Record<string, MutablePuzzleState>>({}); // actor_id -> puzzle_state

  function setPuzzleState(puzzle_type: string, session_id: string, state: AnyPuzzleState) {
    session_lookup.value[puzzle_type] = session_id;
    puzzle_states.value[session_id] = reactive(state);
  }

  // user game sessions
  const getState = (session_id: string) => puzzle_states.value[session_id] ?? null;
  const getSessionID = (puzzle_type: string) => session_lookup.value[puzzle_type] ?? null;
  const setPuzzleSolved = (session_id: string, solved: boolean) => (puzzle_solved.value[session_id] = solved);
  const isPuzzleSolved = (session_id: string) => puzzle_solved.value[session_id];
  const clearSolvedState = (session_id: string) => delete puzzle_solved.value[session_id];

  // admin monitoring view
  const setMonitoredPuzzleState = (actor_id: string, state: AnyPuzzleState) =>
    (monitored_users_games.value[actor_id] = reactive(state));
  const clearMonitoredPuzzleState = (actor_id: string) => delete monitored_users_games.value[actor_id];

  return {
    puzzle_states,
    puzzle_solved,
    session_lookup,

    setPuzzleState,
    getState,
    getSessionID,

    setPuzzleSolved,
    isPuzzleSolved,
    clearSolvedState,

    monitor_user_count,
    monitored_users_games,
    setMonitoredPuzzleState,
    clearMonitoredPuzzleState,
  };
});

function mapButtonToName(button: number): "left" | "right" | "middle" | "unknown" {
  // prettier-ignore
  switch (button) {
    case 0: return "left";
    case 1: return "middle";
    case 2: return "right";
    default: return "unknown";
  }
}

/**
 * This composable provides a reactive interface to the WebSocket server.
 * This should not be used directly, but instead through the `usePuzzleState` composable,
 * or, through a call to `inject<ReturnType<typeof usePuzzleSocket>>("puzzle_socket")`,
 * as it's created and provided in the main.ts file.
 */
export function usePuzzleSocket() {
  ////////////////////////////////////////////////////////////////////////
  //// WebSocket
  //// Connect to the WebSocket server
  const store = useActivePuzzleStore();
  const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  const url = `${protocol}://${window.location.host}/ws/puzzle/`;
  const { send } = useWebSocket(url, {
    autoReconnect: true,
    onMessage: (_ws, event) => handle_message(event),
  });

  ////////////////////////////////////////////////////////////////////////
  //////// Socket Reactivity
  function handle_message(message: MessageEvent) {
    const msg = JSON.parse(message.data) as WebSocketMessage;
    // console.log("websocket message", msg);

    switch (msg.type) {
      case "event:state":
        const state = msg.data as AnyPuzzleState;
        const session_id = msg.session_id;
        if (session_id && state.puzzle_type) {
          store.setPuzzleState(state.puzzle_type, session_id, state);
          if (state.is_solved) {
            store.setPuzzleSolved(session_id, state.is_solved);
          }
        }
        break;

      case "event:submit_result":
        const result = msg.data as SubmitResult;
        if (msg.session_id) store.setPuzzleSolved(msg.session_id, result.is_solved);
        break;

      case "event:error":
        console.error("server websocket error", msg.data);
        break;

      case "event:monitor:state":
        if (!msg.actor_id) {
          console.warn("monitor:state message without actor_id");
          return;
        }
        store.setMonitoredPuzzleState(msg.actor_id, msg.data);
        break;
      case "event:monitor:user_count":
        const res = msg.data as UserCountResult;
        store.monitor_user_count = res.user_count;
        break;
      case "event:monitor:disconnect":
        if (!msg.actor_id) {
          console.warn("monitor:disconnect message without actor_id");
          return;
        }
        store.clearMonitoredPuzzleState(msg.actor_id);
        break;
      default:
        console.warn(`Unknown message type: ${msg.type}`);
    }
  }

  ////////////////////////////////////////////////////////////////////////
  //////// WebSocket User Actions
  function send_command<T>(command: string, data: T, session_id?: string) {
    // console.log(`send_command [${command}]`, data);
    const message: WebSocketMessage<T> = { type: `cmd:${command}`, data };
    if (session_id) message.session_id = session_id;
    send(JSON.stringify(message));
  }

  function getPuzzleSession(puzzle_type: string) {
    const session_id = computed(() => store.getSessionID(puzzle_type));
    const state = computed(() => store.getState(session_id.value));

    // Also watch for session_id changes to handle manual resume/create requests
    watch(
      session_id,
      (new_session_id) => {
        if (new_session_id) {
          send_command("resume", { puzzle_type }, new_session_id); // Try to resume existing session
        } else {
          send_command("create", { puzzle_type }); // Create new session if none exists
        }
      },
      { immediate: true, once: true },
    );

    return {
      // Game State
      state,
      session_id,
      is_ready: computed(() => !!state.value && !!session_id.value),

      // Board Rendering
      rows: computed(() => state.value?.rows ?? 0),
      cols: computed(() => state.value?.cols ?? 0),
      is_solved: computed(() => store.isPuzzleSolved(session_id.value)),
      // is_solved: false,

      // User Input + Interaction
      // Board Actions
      handle_cell_click: (cell: Cell, button: number = 0, state_override?: number) => {
        if (!session_id.value) return;
        store.clearSolvedState(session_id.value);
        let payload: ActionPayload = {
          target: "cell",
          action: "click",
          position: { zone: cell.zone, row: cell.row, col: cell.col, button: mapButtonToName(button) },
        };
        if (state_override !== undefined) {
          payload.position.state = state_override;
        }
        send_command("action", payload, session_id.value);
      },

      // Game Actions
      cmd_puzzle_reset: () => {
        if (!session_id.value) return;
        send_command("reset", {}, session_id.value);
        // store.clearSolvedState(session_id.value);
      },
      cmd_puzzle_create(puzzle_size: string, puzzle_difficulty: string) {
        send_command("create", { puzzle_type, puzzle_size, puzzle_difficulty });
        store.clearSolvedState(session_id.value);
      },
      cmd_puzzle_submit() {
        if (!session_id.value) return;
        send_command("submit", {}, session_id.value);
      },
      clear_solved_state() {
        if (!session_id.value) return;
        // store.clearSolvedState(session_id.value);
      },
    };
  }

  return {
    getPuzzleSession,
    cmd_puzzle_monitor: () => send_command("admin:monitor", {}),
    cmd_puzzle_unmonitor: () => send_command("admin:unmonitor", {}),
  };
}
