import { getRandomPuzzle } from "@/services/app";
import { PuzzleTimer } from "@/services/puzzle.timer";
import { useLocalStorage } from "@vueuse/core";
import { defineStore } from "pinia";
import { computed, ref, watch } from "vue";

export const enum GameResultStatus {
  Idle = "idle",
  Checking = "checking",
  Correct = "correct",
  Wrong = "wrong",
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
      console.log(`NEW GAME FOR ${game_type}`, raw);
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

    const time_started = computed({
      get: () => store.value[key].time_started,
      set: (val: number) => (store.value[key].time_started = val),
    });
    const time_completed = computed({
      get: () => store.value[key].time_completed,
      set: (val: number | undefined) => (store.value[key].time_completed = val),
    });

    // Computed variables for easy referencing of other values (probably not to be exported)
    const is_solved = computed(() => time_completed.value !== undefined);

    // Refs that are used for this puzzle
    const game_result_status = ref<GameResultStatus>(
      is_solved.value ? GameResultStatus.Correct : GameResultStatus.Idle,
    );
    const timer = new PuzzleTimer(time_started, time_completed);

    // Watches + Intervals
    /* reset when the user edits the board */
    watch(
      () => wrapper.value,
      () => {
        game_result_status.value = GameResultStatus.Idle;
      },
      { deep: true },
    );
    watch(is_solved, (solved) => {
      if (solved && game_result_status.value !== GameResultStatus.Correct) {
        game_result_status.value = GameResultStatus.Correct;
      } else if (!solved && game_result_status.value === GameResultStatus.Correct) {
        game_result_status.value = GameResultStatus.Idle;
      }
    });

    // Create functions relevate to the puzzle
    function push_event(event_name: string, payload?: any) {
      wrapper_history.value.push({ ts: Date.now(), type: event_name, payload });
    }
    function puzzle_reset() {
      if (is_solved.value) return;
      const fresh = adapter.empty_state(store.value[key].raw);
      Object.assign(store.value[key].state, fresh);
      wrapper_history.value = [{ ts: Date.now(), type: "fetch" }];
    }

    async function puzzle_check_solution() {
      game_result_status.value = GameResultStatus.Checking;
      const solved = await adapter.validate(wrapper.value, store.value[key].raw);
      if (solved === true) {
        game_result_status.value = GameResultStatus.Correct;
        timer.complete();
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
      is_solved,
    };
  }

  return { usePuzzle };
});
