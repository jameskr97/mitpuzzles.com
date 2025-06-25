import type { NetDriver } from "@/services/transport/netdriver.ts";
import mitt, { type Emitter } from "mitt";
import { type Ref, ref } from "vue";
import type { CommandIdentify, Payload, WebsocketEnvelope } from "@/codegen/websocket/envelope.schema";
import type {
  CommandAction,
  CommandClear,
  CommandLoad,
  CommandRefresh, CommandResume, CommandSubmit, CommandToggleTutorial, EventState, EventSubmitResult,
  PayloadPuzzleType
} from "@/codegen/websocket/game.schema";

type Events = {
    connected: void;
    state: EventState;
    submit_result: boolean;
};

/**
 * Service for managing game interactions.
 */
export interface IGameService {
  // Game Events
  readonly bus: Emitter<Events>;
  readonly connected: Ref<boolean>;
  load: (puzzle_type: string) => void;
  resume: (attempt_id: string) => void;
  refresh: (game_id: string, size?: string, difficulty?: string) => void;
  action: (action: CommandAction) => void;
  clear: (game_id: string) => void;
  submit: (game_id: string) => void;

  // Game States
  setTutorialEnabled: (session_id: string, enabled: boolean) => void;
}

export class WebsocketGameService implements IGameService {
  readonly bus = mitt<Events>();
  readonly connected = ref(false);
  private pending: Payload[] = [];
  private identified = false;

  constructor(private net: NetDriver) {
    this.net.bus.on("message", (m) => this.#route(m));
    this.net.bus.on("open", () => this.#autoIdentify());
  }

  connect = () => this.net.open();
  close = () => {
    this.net.close();
    this.connected.value = false;
  }

  load = (puzzle_type: string) => this.#send<CommandLoad>({ kind: "load", puzzle_type: puzzle_type as PayloadPuzzleType });
  resume = (attempt_id: string) => this.#send<CommandResume>({ kind: "resume", session_id: attempt_id });
  refresh = (session_id: string, size?: string, difficulty?: string) => this.#send<CommandRefresh>({ kind: "refresh", session_id, size, difficulty });
  action = (action: CommandAction) => this.#send<CommandAction>(action);
  clear = (session_id: string) => this.#send<CommandClear>({ kind: "clear", session_id });
  submit = (session_id: string) => this.#send<CommandSubmit>({ kind: "submit", session_id });
  setTutorialEnabled = (session_id: string, enabled: boolean) => this.#send<CommandToggleTutorial>({ kind: "toggle_tutorial", session_id, enabled });

  #send<T extends Payload>(payload: T) {
    if (this.net.state === "OPEN" && this.identified) {
      this.net.send(payload.kind, payload);
    } else {
      this.pending.push(payload)
    }
  }
  #route(env: WebsocketEnvelope) {
    switch (env.kind) {
      case "identified":
        this.identified = true;
        this.connected.value = true;
        this.pending.forEach(packet => this.net.send(packet.kind, packet));
        this.pending.length = 0;
        this.bus.emit("connected");
        break
      case "state":
        this.bus.emit("state", env.payload as EventState);
        break;
      case "submit_result":
        const res = env.payload as EventSubmitResult
        this.bus.emit("submit_result", res.solved);
        break;
    }
  }
  #autoIdentify() {
    const url = new URL(window.location.href);
    const mode =
      /^\/experiment\//.test(location.pathname) || /^\/devtools\/test-experiment/.test(location.pathname)
        ? "prolific"
        : "freeplay";

    let payload: CommandIdentify = { kind: "identify", mode };
    if (mode === "prolific") {
      payload.prolific_subject_id = url.searchParams.get("PROLIFIC_PID") || undefined;
      payload.prolific_session_id = url.searchParams.get("SESSION_ID") || undefined;
      payload.prolific_study_id = url.searchParams.get("STUDY_ID") || undefined;
    }

    this.net.send<CommandIdentify>(payload.kind, payload);
  }
}

