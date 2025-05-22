import { type BoardEvents } from "@/features/games.components/board.interaction.ts";
import { usePuzzleState } from "@/composables/usePuzzleState.ts";
import { useDragStateChanger } from "@/features/games.composables/useDragStateChanger.ts";
import { useClearStateBehaviour } from "@/features/games.composables/useClearStateBehaviour.ts";
import { useStateCycleBehaviour } from "@/features/games.composables/useStateCycleBehaviour.ts";
import { watch } from "vue";

type GameEvents = {
  onBoardModified: (board: number[]) => void;
};

/**
 * Create a bridge between the puzzle interaction and the puzzle state.
 * - This allows users to add custom behaviours to the puzzle interaction.
 * - Default global behaviours are added by default.
 * - Note, the order of the behaviours is important, as they are called in the order they are added.
 * @param session
 */
export function createPuzzleInteractionBridge(session: Awaited<ReturnType<typeof usePuzzleState>>) {
  // any key in BoardEvents is a key the user can use to watch for the events the care about
  type EventHandlerListKey = keyof BoardEvents;
  // a list of functions that take any number of arguments and return a boolean (because all the events in BoardEvents return a boolean)
  type EventHandlerList = ((...args: any[]) => boolean)[];
  const handlerMap: Partial<Record<EventHandlerListKey, EventHandlerList>> = {};

  /**
   * Add a behaviour to the bridge. This is a function that takes the session, to allow
   * each of the functions to access the session + state.
   * @param behaviour
   */
  function addInputBehaviour<T extends Partial<BoardEvents>>(behaviour: (puzzle: typeof session) => T): T {
    const additions = behaviour(session);

    // For each of the `BoardEvent` keys in the behaviour
    for (const key in additions) {
      // typecast the key to the correct type, and get a
      // reference the function for that key
      const typedKey = key as keyof BoardEvents;
      const fn = additions[typedKey];

      // if it's a function then add it to the list of handlers
      if (typeof fn === "function") {
        // create an empty list if it doesn't exist
        if (!handlerMap[typedKey]) handlerMap[typedKey] = [];

        // add that handler to the list
        handlerMap[typedKey]!.push(fn);
      }
    }

    return additions;
  }

  /**
   * Compile all the handlers together into a single object that can be used.
   * If any of the handlers returns true, then the event is considered handled,
   * and propagation will not continue.
   */
  function getBridge(include_default_behaviours: boolean = true): Partial<BoardEvents> {
    // Add the default behaviors
    if (include_default_behaviours) {
      addInputBehaviour(useClearStateBehaviour);
      addInputBehaviour(useStateCycleBehaviour);
      addInputBehaviour(useDragStateChanger);
    }

    const combined: Partial<BoardEvents> = {};

    // for each key in the compiled handlerMap
    for (const key in handlerMap) {
      // typecast the key to the correct type, and get a reference
      // to the list of functions for that key
      const typedKey = key as keyof BoardEvents;
      const fns = handlerMap[typedKey]!;

      // create an anonymous function that calls all the functions in the list
      combined[typedKey] = (...args: any[]): boolean => {
        // call every function compiled together (the above EventHandlerList) in the list and passthrough any arguments
        for (const fn of fns) {
          const res = fn(...args); // Note EventHandlerList above all return a boolean
          if (res) return true; // if a function returns true, it means the event is handled, stop calling
        }
        return false; // if no function returns true, return false
      };
    }

    return combined;
  }

  type GameEventHandlerListKey = keyof GameEvents;
  type GameEventHandlerList = ((...args: any[]) => void)[];
  const gameEventHandlers: Partial<Record<GameEventHandlerListKey, GameEventHandlerList>> = {};
  function emitGameEvent<K extends keyof GameEvents>(event: K, ...args: Parameters<GameEvents[K]>) {
    for (const fn of gameEventHandlers[event] || []) {
      fn(...args);
    }
  }

  /** Identical to addInputBehaviour, but for game events, and adds to different list */
  function addGameBehaviour(behaviour: (puzzle: typeof session) => Partial<GameEvents>) {
    const additions = behaviour(session);
    for (const key in additions) {
      const typedKey = key as keyof GameEvents;
      const fn = additions[typedKey];
      if (typeof fn === "function") {
        if (!gameEventHandlers[typedKey]) gameEventHandlers[typedKey] = [];
        gameEventHandlers[typedKey]!.push(fn);
      }
    }
  }

  watch(
    // Safely access .board only if session.state.value is not null
    () => (session.state.value ? session.state.value.board : null),
    (new_board) => {
      // Now, new_board can be null if session.state.value was null,
      // or if session.state.value.board was null.
      // We still only want to emit if new_board is a valid board array.
      if (new_board && Array.isArray(new_board)) {
        emitGameEvent("onBoardModified", new_board);
      }
    },
    { immediate: false, deep: false },
  );

  return {
    addInputBehaviour,
    getBridge,
    addGameBehaviour,
  };
}
