import { useLocalStorage } from "@vueuse/core";
import { ref, reactive } from "vue";
import { defineStore } from "pinia";
import type { MutablePuzzleState, AnyPuzzleState } from "@/services/states.ts";

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
