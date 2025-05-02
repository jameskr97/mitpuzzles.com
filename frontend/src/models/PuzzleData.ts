import logger from "@/services/logger.ts";
import { computed, type ComputedRef, ref, type Ref } from "vue";
import { useLocalStorage } from "@vueuse/core";
import { getUnsolvedPuzzle, getUnsolvedPuzzleCount, submitGameRecording } from "@/services/app.ts";
import { useDelayedLoader } from "@/composables/useDelayedLoader.ts";
import { PuzzleTimer } from "@/utils.ts";

export const enum GameUIState {
  Ready,
  CheckingSolution,
  Correct,
  Wrong,
  Loading, // when the puzzle is being loaded/fetched from the servers
  NoPuzzles, // when there are no puzzles left to solve
}

interface ErrorRecord {
  load: Error | null;
}

const errorsFactory = (): ErrorRecord => ({
  load: null,
});

interface HistoryEntry {
  ts: number;
  type: string;
  payload?: any;
}

/**
 * Adapter to be used in the usePuzzleStore
 * @param Raw The raw payload from the backend
 * @param State The client-side structure
 */
interface RawWithGeneral {
  id: number;
  timestamp: string; // the time the game was retrieved from the server
  [key: string]: any; // allow any other properties
}

/**
 * Adapter for converting raw board games to client-side board games,
 * and for validating games client-side.
 * @param Raw The raw payload from the backend
 * @param State The client-side structure
 */
export interface PuzzleAdapter<Raw extends RawWithGeneral, State = Raw> {
  /**
   * Convert the payload from the backend into the client-side structure
   * @param raw The raw payload from the backend
   */
  create_state(raw: Raw): State;

  /**
   * Validate the game board with the solution hash from the backend
   * or agains another solution
   * @param raw The raw payload from the backend
   * @returns True if the game is solved, false otherwise
   */
  validate(state: State, raw: Raw): Promise<boolean> | boolean;


  /**
   * Check if the game can be validated.
   * We don't want the user to submit the game unless they have made all possible changes.
   * @param state
   * @param raw
   */
  can_validate(state: State, raw: Raw): boolean;
}

export class PuzzleData<Raw extends RawWithGeneral, State> {
  // local storage references to the game
  readonly key: string;
  private _gamedata: Ref<Raw | undefined>;
  private _state: Ref<State | undefined>;
  private _history: Ref<HistoryEntry[]>;
  private _submitted: Ref<boolean>;
  /// time variables
  private _time_elapsed: Ref<number>;
  private _time_completed: Ref<boolean>;
  readonly timer: PuzzleTimer;

  // reactive states for this puzzle instances
  readonly can_render_board: ComputedRef<boolean>;
  readonly error: Ref<ErrorRecord> = ref(errorsFactory());
  readonly ui: Ref<GameUIState> = ref(GameUIState.Loading);

  // loader
  private loader = useDelayedLoader();

  constructor(
    private GAME_TYPE: string,
    private GAME_VARIANT: string,
    private adapter: PuzzleAdapter<Raw, State>,
  ) {
    logger.info(`PuzzleSession created for game type: ${GAME_TYPE}`);

    // get references to localstorage
    this.key = `mitlogic.puzzles:${GAME_TYPE}:${GAME_VARIANT}`;
    this._gamedata = useLocalStorage<Raw | undefined>(`${this.key}:gamedata`, {} as any);
    this._state = useLocalStorage<State | undefined>(`${this.key}:state`, {} as any);
    this._history = useLocalStorage<HistoryEntry[]>(`${this.key}:history`, []);
    this._submitted = useLocalStorage<boolean>(`${this.key}:submitted`, false);
    this._time_elapsed = useLocalStorage<number>(`${this.key}:time_elapsed`, 0);
    this._time_completed = useLocalStorage<boolean>(`${this.key}:time_completed`, false);
    this.timer = new PuzzleTimer(this._time_elapsed, this._time_completed);
    this.can_render_board = computed(
      () => this.is_state_valid() && this.is_gamedata_valid() && this.ui.value !== GameUIState.NoPuzzles,
    );
  }

  async init() {
    // Query if there are any unsolved puzzles available for this game type
    try {
      const res = await getUnsolvedPuzzleCount({ puzzle_type: this.GAME_TYPE });
      if (res.data.unsolved_count === 0) {
        logger.info(`No puzzles available for ${this.GAME_TYPE}`);
        this.ui.value = GameUIState.NoPuzzles;
        return;
      }
    } catch (err: any) {}

    // check if current puzzle already submitted
    if (this._submitted.value) {
      this.ui.value = GameUIState.Correct;
      return;
    }

    // invariant - there is a puzzle for this user to solve
    if (this.is_state_valid() && this.is_gamedata_valid()) {
      this.ui.value = GameUIState.Ready;
      this.timer.start();
      return;
    }
    // invariant - stored data is invalid; retrieve new
    logger.debug(`Detected missing puzzle data for ${this.key}; requesting new puzzle.`);
    await this.load_new_puzzle();
  }

  // Validation
  private is_gamedata_valid(): boolean {
    return (
      !!this._state.value && typeof this._gamedata.value === "object" && Object.keys(this._gamedata.value).length != 0
    );
  }

  private is_state_valid(): boolean {
    return !!this._state.value && typeof this._state.value === "object" && Object.keys(this._state.value).length != 0;
  }

  // property getters
  // // UI state getters
  get puzzle_id(): number {
    return this._gamedata.value?.id ?? -1;
  }

  get ready(): boolean {
    return this.ui.value === GameUIState.Ready;
  }

  get loading(): boolean {
    return this.loader.showSpinner.value;
  }

  get checking(): boolean {
    return this.ui.value === GameUIState.CheckingSolution;
  }

  get correct(): boolean {
    return this.ui.value === GameUIState.Correct;
  }

  get wrong(): boolean {
    return this.ui.value === GameUIState.Wrong;
  }

  get no_puzzles(): boolean {
    return this.ui.value === GameUIState.NoPuzzles;
  }

  get can_submit(): boolean {
    return this.adapter.can_validate(this.state.value!, this._gamedata.value!)
  }

  get history(): HistoryEntry[] {
    return this._history.value;
  }

  get state(): Ref<State | undefined> {
    if (!this.is_state_valid() && this.is_gamedata_valid()) {
      logger.warn(`State was invalid; regenerating from game_data for ${this.key}`);
      this._state.value = this.adapter.create_state(this._gamedata.value!);
    }
    return this._state;
  }

  // Actions
  /** Clear the current puzzle state and reset to the initial state */
  clear_state() {
    if (!this.is_gamedata_valid() && !this.is_state_valid()) return;
    Object.assign(this._state.value!, this.adapter.create_state(this._gamedata.value!));
    this.record_event("clear_clicked");
  }

  /** Request a new puzzle from the backend */
  async load_new_puzzle() {
    logger.debug(`Loading new puzzle for ${this.key}`);

    try {
      // Request a new puzzle from the backend + Reset History
      const res = await this.loader.run(async () => (await getUnsolvedPuzzle({ puzzle_type: this.GAME_TYPE })).data);
      this._history.value = [];

      // Determine the type of response
      if (res.type === "empty_puzzle_set") {
        // No puzzles available for this game type, set UI state accordingly
        logger.info(`No puzzles found for ${this.GAME_TYPE}`);
        this.ui.value = GameUIState.NoPuzzles;
      } else if (res.type === "Puzzle") {
        // We have a valid puzzle, set the game data and state
        // store puzzle data
        this._gamedata.value = res.data as Raw;
        this._submitted.value = false;
        Object.assign(this._state.value!, this.adapter.create_state(this._gamedata.value));
        // reset timer
        this.timer.reset();
        this.timer.start();
        this.ui.value = GameUIState.Ready;
        this.error.value.load = null;
      }
    } catch (err: any) {
      logger.error(`Error loading new puzzle for ${this.key}`);
      console.log(err);
      // this.error.value.load = err.response.data;
    }
  }

  /**
   * Uses adapter to validate the current game state.
   */
  async submit_solution(): Promise<boolean> {
    if (this._submitted.value) {
      logger.warn(`Cannot submit solution for ${this.GAME_TYPE} (${this.GAME_VARIANT}) - already marked submitted.`);
      return false;
    }
    if (!this.is_gamedata_valid()) {
      logger.warn(`Cannot submit solution for ${this.GAME_TYPE} (${this.GAME_VARIANT}) - no game data available.`);
      return false;
    }
    logger.debug(`Checking solution for ${this.GAME_TYPE} (${this.GAME_VARIANT})`);
    const solved = await this.adapter.validate(this.state.value!, this._gamedata.value!);
    this.ui.value = solved ? GameUIState.Correct : GameUIState.Wrong;
    this.record_event("check_solution_clicked", { solved });
    if (!solved) return false;
    // invariant - solution is correct

    const res = await submitGameRecording(this._gamedata.value!.id, this._gamedata.value!.timestamp, {
      history: this._history.value,
    });
    this.timer.complete();
    if (res.status === 201) {
      this._submitted.value = true;
      logger.debug(`Submitted solution for ${this.GAME_TYPE} (${this.GAME_VARIANT})`, res);
    } else {
      logger.error(`Failed to submit solution for ${this.GAME_TYPE} (${this.GAME_VARIANT})`, res);
    }

    return solved;
  }

  /**
   * Record an event in the history
   * Note:
   * @param type the name of the event
   * @param payload the data associated with the event
   */
  record_event(type: string, payload?: object) {
    let event = { ts: Date.now(), type, payload };
    // TODO(james): uncomment this line and properly change the log level in prod
    // logger.trace(`Event recorded: ${event}`);
    this._history.value.push(event);
  }
}
