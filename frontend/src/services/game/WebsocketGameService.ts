import type { NetDriver } from "@/services/transport/netdriver.ts";
import mitt, { type Emitter, type EventType } from "mitt";
import { type Ref, ref } from "vue";
import type {
  CommandExperimentInit,
  CommandExperimentStep,
  CommandIdentify,
  EventExperimentState, EventIdentified,
  Payload,
  WebsocketEnvelope
} from "@/codegen/websocket/envelope.schema";
import type {
  CommandAction,
  CommandClear,
  CommandLoad,
  CommandMistakeCount,
  CommandRefresh,
  CommandResume,
  CommandSubmit,
  CommandToggleTutorial,
  EventState,
  EventSubmitResult,
  PayloadPuzzleType, SupportedPuzzleTypes
} from "@/codegen/websocket/game.schema";
import type { CommandExperimentConsent } from "@/codegen/websocket/experiment.schema";

type Events = {
  connected: void;
  state: EventState;
  submit_result: boolean;

  experiment_state: string;
};

/**
 * Service for managing game interactions.
 */
export interface IGameService<T extends Record<EventType, unknown>> {
  // Game Events
  readonly bus: Emitter<T>;
  readonly connected: Ref<boolean>;
  load: (puzzle_type: string) => void;
  resume: (puzzle_type: string, attempt_id: string) => void;
  refresh: (game_id: string, puzzle_type: string, size?: string, difficulty?: string) => void;
  action: (action: CommandAction) => void;
  clear: (game_id: string, puzzle_type: string) => void;
  submit: (game_id: string, puzzle_type: string, duration: number) => void;
  send: <T extends Payload>(payload: T) => void;

  // Game States
  setTutorialEnabled: (session_id: string, puzzle_type: string, enabled: boolean) => void;
}

export class WebsocketGameService implements IGameService<Events> {
  readonly bus = mitt<Events>();
  readonly connected = ref(false);
  private pending: Payload[] = [];
  private identified = false;
  public identity_mode: "freeplay" | "prolific" | null = null;

  constructor(private net: NetDriver) {
    this.net.bus.on("message", (m) => this.#route(m));
    this.net.bus.on("open", () => this.autoIdentify());
  }

  connect = () => this.net.open();
  close = () => {
    this.net.close();
    this.connected.value = false;
  }

  load = (puzzle_type: string) =>
    this.send<CommandLoad>({
      kind: "load",
      puzzle_type: puzzle_type as PayloadPuzzleType,
    });
  resume = (puzzle_type: string, attempt_id: string) =>
    this.send<CommandResume>({
      kind: "resume",
      attempt_id,
      puzzle_type,
    });
  refresh = (attempt_id: string, puzzle_type: string, size?: string, difficulty?: string) => this.send<CommandRefresh>({ kind: "refresh", attempt_id, puzzle_type, size, difficulty });
  action = (action: CommandAction) => this.send<CommandAction>(action);
  clear = (attempt_id: string, puzzle_type: string) => this.send<CommandClear>({ kind: "clear", attempt_id, puzzle_type});
  submit = (attempt_id: string, puzzle_type: string, duration: number) =>
    this.send<CommandSubmit>({
      kind: "submit",
      puzzle_type,
      attempt_id,
      client_duration: duration,
    });
  setTutorialEnabled = (attempt_id: string, puzzle_type: string, enabled: boolean) =>
    this.send<CommandToggleTutorial>({
      kind: "toggle_tutorial",
      puzzle_type,
      attempt_id,
      enabled,
    });
  send<T extends Payload>(payload: T) {
    if (this.net.state === "OPEN" && this.identified) {
      this.net.send(payload.kind, payload);
    } else {
      this.pending.push(payload);
    }
  }

  #route(env: WebsocketEnvelope) {
    switch (env.payload.kind) {
      case "identified":
        const data = env.payload as EventIdentified;
        this.identified = true;
        this.identity_mode = data.mode
        this.connected.value = true;
        this.pending.forEach((packet) => this.net.send(packet.kind, packet));
        this.pending.length = 0;
        this.bus.emit("connected");
        break;
      case "state":
        this.bus.emit("state", env.payload as EventState);
        break;
      case "submit_result":
        const res = env.payload as EventSubmitResult;
        this.bus.emit("submit_result", res.solved);
        break;

      case "event_experiment_state":
        const state = env.payload as EventExperimentState;
        this.bus.emit("experiment_state", state);
        break;
    }
  }

  autoIdentify() {
    const url = new URL(window.location.href);
    const IS_TEST_EXPERIMENT = /^\/devtool\/test-experiment/.test(location.pathname);
    const IS_REAL_EXPERIMENT = /^\/experiment\//.test(location.pathname);
    const mode = IS_TEST_EXPERIMENT || IS_REAL_EXPERIMENT ? "prolific" : "freeplay";

    // set fake url params if test
    // set each one to random value with a prefix of TEST_
    if (IS_TEST_EXPERIMENT) {
      const getOrCreateTestId = (key: string): string => {
        const storageKey = `testExp_${key}`;
        const existingId = localStorage.getItem(storageKey);

        if (existingId) {
          return existingId;
        }

        const newId = `TEST_${Math.random().toString(36).substring(2, 15)}`;
        localStorage.setItem(storageKey, newId);
        return newId;
      };
      url.searchParams.set("PROLIFIC_PID", getOrCreateTestId("PROLIFIC_PID"));
      url.searchParams.set("SESSION_ID", getOrCreateTestId("SESSION_ID"));
      url.searchParams.set("STUDY_ID", getOrCreateTestId("STUDY_ID"));
      url.searchParams.set("EXPERIMENT_ID", `5f42a9e4-0018-4653-9068-e24ed19ac5e8`);
    }

    let payload: CommandIdentify = { kind: "identify", mode };
    if (mode === "prolific") {
      payload.prolific_subject_id = url.searchParams.get("PROLIFIC_PID") || undefined;
      payload.prolific_session_id = url.searchParams.get("SESSION_ID") || undefined;
      payload.prolific_study_id = url.searchParams.get("STUDY_ID") || undefined;
      payload.experiment_id = url.searchParams.get("EXPERIMENT_ID") || undefined;
    }

    this.net.send<CommandIdentify>(payload.kind, payload);
  }

  // Experiment Events
  consent = () => {
    this.send<CommandExperimentConsent>({ kind: "experiment_consent" });
  };
  set_step = (step_name: string) => this.send<CommandExperimentStep>({ kind: "experiment_step", step_name });
  // complete = () => this.#send({ kind: "complete", timestamp: Date.now() });
}
