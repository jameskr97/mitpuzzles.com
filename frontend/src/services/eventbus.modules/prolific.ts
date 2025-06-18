import type { AnyPuzzleState, MutablePuzzleState } from "@/services/states.ts";
import { emit, on } from "@/services/eventbus.ts";
import type { WebSocketMessage } from "@/services/eventbus.modules/websocket.ts";
import type { Cell } from "@/features/games.components/board.interaction.ts";
import { useCurrentExperiment } from "@/store/useCurrentExperiment.ts";
import { ref } from "vue";

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

export const prolificModule = {
  name: "prolific",
  setup(): GameModuleInterface {
    ////////////////////////////////////////////////////////////////////////
    // State Management
    const experiment = useCurrentExperiment();
    const current_puzzle = ref<MutablePuzzleState>({});

    ////////////////////////////////////////////////////////////////////////
    // Helpers
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

    unsub_funcs.push(on("prolific:state", (event: WebSocketMessage<AnyPuzzleState>) => {
      current_puzzle.value = event.data as MutablePuzzleState;
    }));
    // unsub_funcs.push(on("game:set_active_puzzle", (x) => (activePuzzleType = x)));
    // unsub_funcs.push(on("prolific:submit", (event: WebSocketMessage<boolean>) => {
    // }));

    return {
      resumePuzzle(_puzzle_type: string) {
        send_command("prolific:resume", {});
      },
      getPuzzleState(_session_id: string): MutablePuzzleState | undefined {
        return current_puzzle.value
      },
      getSessionID(_puzzleType: string): string | undefined {
        return "session_id";
      },
      clear_solved_state() {},
      clear_puzzle_state() {},
      get_solved_state(): boolean { return false},
      handle_cell_click(cell: Cell, button: number = 0, state_override?: number) {
        let payload: ActionPayload = {
          target: "cell",
          action: "click",
          position: { zone: cell.zone, row: cell.row, col: cell.col, button: mapButtonToName(button) },
        };
        if (state_override !== undefined) {
          payload.position.state = state_override;
        }

        send_command("prolific:action", payload);
      },

      toggle_tutorial(_enabled: boolean) {},
      request_new_puzzle(_puzzle_size: string | undefined, _puzzle_difficulty: string | undefined) {},
      request_submit() {
        send_command("prolific:submit", {});
      },

      _cleanup() {
        unsub_funcs.forEach((func) => func());
      },
    };
  },
};
