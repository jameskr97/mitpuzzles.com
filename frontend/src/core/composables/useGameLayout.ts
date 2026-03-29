import { defineStore } from "pinia";
import { useLocalStorage } from "@vueuse/core";
import { computed } from "vue";

export type GameLayoutReturn = ReturnType<typeof useGameLayout>;

export function useGameLayout(puzzle_type: string, options?: { auto_show_instructions?: boolean }) {
  const store = useGameLayoutStore();
  const auto_show = options?.auto_show_instructions ?? true;

  // has user ever seen instructions for this puzzle type?
  const hasSeenInstructions = computed(() => store.hasVisitedGame(puzzle_type));

  // auto-show on first visit only if auto_show is enabled (freeplay yes, daily no)
  const instructions_visible = computed({
    get: () => (auto_show && !hasSeenInstructions.value) || store.booleanFor("instructions", false).value,
    set: (value) => {
      if (!hasSeenInstructions.value) {
        // opening or closing instructions marks this puzzle type as seen
        store.markGameAsVisited(puzzle_type);
      }
      store.booleanFor("instructions", false).value = value;
    },
  });

  const leaderboard_visible = store.booleanFor("leaderboard");

  return {
    instructions_visible,
    leaderboard_visible,
    toggle_instructions: () => (instructions_visible.value = !instructions_visible.value),
    toggle_leaderboard: () => (leaderboard_visible.value = !leaderboard_visible.value),
    hasSeenInstructions,
  };
}

export const useGameLayoutStore = defineStore("mitlogic.layout", () => {
  const store = useLocalStorage<Record<string, boolean>>("mitlogic.gamelayout", {});
  const visitedGames = useLocalStorage<Record<string, boolean>>("mitlogic.visited_games", {});

  function booleanFor(flag: string, defaultValue = true) {
    return computed<boolean>({
      get: () => store.value[flag] ?? defaultValue,
      set: (v) => (store.value[flag] = v),
    });
  }

  function hasVisitedGame(gameType: string) {
    return Boolean(visitedGames.value[gameType]);
  }

  function markGameAsVisited(gameType: string) {
    visitedGames.value[gameType] = true;
  }

  return {
    booleanFor,
    hasVisitedGame,
    markGameAsVisited,
  };
});
