import { getRandomPuzzle } from "@/api/app";
import { GameResultStatus } from "@/api/types";
import { format_game_stopwatch } from "@/lib/util";
import { useLocalStorage } from "@vueuse/core";
import { defineStore } from "pinia";
import { computed, ref, watch, type Ref, type ComputedRef } from "vue";

export class PuzzleTimer {
  private intervalId: number | null = null;

  private time_started: Ref<number>;
  private time_completed: Ref<number | undefined>;
  time_elapsed: Ref<number>;
  display_time: ComputedRef<string>;

  constructor(time_started: number, time_completed?: number) {
    this.intervalId = null;
    this.time_started = ref(time_started);
    this.time_completed = ref(time_completed);
    this.time_elapsed = ref(0);
    this.display_time = computed(() => format_game_stopwatch(this.time_elapsed.value));

    this.updateScreenTime();
    watch(
      [this.time_started, this.time_completed],
      () => {
        if (this.time_completed.value === undefined) {
          this.updateScreenTime();
          if (this.intervalId === null) {
            this.intervalId = setInterval(this.updateScreenTime, 1000);
          }
        } else {
          if (this.intervalId !== null) {
            clearInterval(this.intervalId);
            this.intervalId = null;
          }
          this.updateScreenTime();
        }
      },
      { immediate: true },
    );
  }

  protected complete() {
    if (this.time_completed.value === null) {
      this.time_completed.value = Date.now();
    }

    this.updateScreenTime();
    if (this.intervalId !== null) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
  }

  reset() {
    this.time_started.value = Date.now();
    this.time_completed.value = undefined;
    this.time_elapsed.value = 0;
  }

  updateScreenTime = () => {
    if (this.time_completed.value !== undefined) {
      this.time_elapsed.value = this.time_completed.value - this.time_started.value;
    } else {
      this.time_elapsed.value = Date.now() - this.time_started.value;
    }
  };

  protected stop() {}
}

/**
 * Adapter to be used in the usePuzzleStore
 * @param Raw The raw payload from the backend
 * @param State The client-side structure
 */
export interface PuzzleAdapter<Raw, State = Raw> {
  /**
   * Convert the payload from the backend into the client-side structure
   * @param raw The raw payload from the backend
   */
  normalize(raw: Raw): State;

  /**
   * Convert the payload from the backend into an empty state
   * Different from normalize: maybe on initial request of a board, some inital state is also
   * sent over to display with the board. This empty state will also clear that.
   * (imagine a board sent with some initial state [a tent already placed], this will clear that)
   * (though without that particular case, this is identical to normalize)
   * @param raw
   */
  empty_state(raw: Raw): State;

  /**
   * Validate the game board with the solution hash from the backend
   * or agains another solution
   * @param state The current state
   * @param raw The raw payload from the backend
   * @returns True if the game is solved, false otherwise
   */
  validate(state: State, raw: Raw): Promise<boolean> | boolean;
}

type Key = `${string}:${string}`; // "type:variant"
interface Stored<Raw, State> {
  /** The raw payload from the backend */
  raw: Raw;
  /** The reactive state the user modifies as they play */
  state: State;
  /** The log of changes as the user plays */
  history: { ts: number; type: string; payload?: any }[];
  /** The time the game was retrieved from the server */
  time_started: number;
  time_completed?: number;
  /** The solution hash from the backend */
  solution_hash?: string;
}

export const usePuzzleStore = defineStore("mitlogic.puzzles", () => {
  /* All game data is stored in this mitlogic.puzzles localstorage entry */
  const store = useLocalStorage<Record<Key, Stored<any, any>>>("mitlogic.puzzles", {});
  const as_key = (t: string, v: string) => `${t}:${v}` as Key;

  async function usePuzzle<Raw, State>(game_type: string, game_variant: string, adapter: PuzzleAdapter<Raw, State>) {
    // Create key, request initial puzzle, create computed wrapper for state modification
    const key = as_key(game_type, game_variant);

    /** Request a new puzzle from the backend, and update existing store, or create new. */
    async function load_new_puzzle() {
      const raw = await getRandomPuzzle(game_type);
      const time_received = Date.now();

      // Don't have data stored. Store new!
      if (!store.value[key]) {
        store.value[key] = {
          raw,
          state: adapter.normalize(raw),
          history: [{ ts: Date.now(), type: "fetch" }],
          time_started: time_received,
        };
      }
      // We do have data stored? Update existing to keep reactivity
      else {
        // Reload: mutate in-place to preserve reactivity
        store.value[key].raw = raw;
        Object.assign(store.value[key].state, adapter.empty_state(raw));
        store.value[key].history = [{ ts: time_received, type: "fetch" }];
        store.value[key].time_started = time_received;
        store.value[key].time_completed = undefined;
      }
    }

    if (!store.value[key]) await load_new_puzzle();

    // Computed wrappers
    const wrapper = computed<State>({ get: () => store.value[key].state, set: (v) => (store.value[key].state = v) });
    const wrapper_history = computed({
      get: () => store.value[key].history,
      set: (v) => (store.value[key].history = v),
    });

    // Refs that are used for this puzzle
    const game_result_status = ref<GameResultStatus>(GameResultStatus.Idle);
    const timer = new PuzzleTimer(store.value[key].time_started);

    // Watches + Intervals
    /* reset when the user edits the board */
    watch(
      () => wrapper.value,
      () => {
        game_result_status.value = GameResultStatus.Idle;
      },
      { deep: true },
    );

    // Create functions relevate to the puzzle
    function push_event(event_name: string, payload?: any) {
      wrapper_history.value.push({ ts: Date.now(), type: event_name, payload });
    }
    function puzzle_reset() {
      const fresh = adapter.empty_state(store.value[key].raw);
      Object.assign(store.value[key].state, fresh);
      wrapper_history.value = [{ ts: Date.now(), type: "fetch" }];
    }
    function puzzle_check_solution() {
      game_result_status.value = GameResultStatus.Checking;
      const solved = adapter.validate(wrapper.value, store.value[key].raw);

      if (solved === true) {
        game_result_status.value = GameResultStatus.Correct;
        push_event("solved");
      } else if (solved === false) {
        game_result_status.value = GameResultStatus.Wrong;
      } else {
        game_result_status.value = GameResultStatus.Idle;
      }

      return solved;
    }
    async function puzzle_request_new() {
      await load_new_puzzle();
      timer.reset();
    }

    return {
      state: wrapper,
      game_result_status,
      history: wrapper_history,
      timer,
      push_event,
      reset: puzzle_reset,
      request_new: puzzle_request_new,
      check_solution: puzzle_check_solution,
    };
  }

  return { usePuzzle };
});
