import { defineStore } from "pinia";
import { useLocalStorage } from "@vueuse/core";
import { useRoute } from "vue-router";
import { computed } from "vue";

export function useGameLayout() {
  const store = useGameLayoutStore();
  const route = useRoute();
  const game_type = route.meta.game_type as string;

  const isFirstVisit = computed(() => !store.hasVisitedGame(game_type));
  const instructions_visible = computed({
    get: () => isFirstVisit.value || store.booleanFor("instructions").value,
    set: (value) => {
      if (isFirstVisit.value && !value) {
        // Mark this game as visited when closing instructions first time
        store.markGameAsVisited(game_type);
      }
      store.booleanFor("instructions").value = value;
    },
  });
  const leaderboard_visible = store.booleanFor("leaderboard");

  return {
    instructions_visible,
    leaderboard_visible,
    toggle_instructions: () => (instructions_visible.value = !instructions_visible.value),
    toggle_leaderboard: () => (leaderboard_visible.value = !leaderboard_visible.value),
    isFirstVisit,
  };
}

export const useGameLayoutStore = defineStore("mitlogic.layout", () => {
  const store = useLocalStorage<Record<string, boolean>>("mitlogic.gamelayout", {});
  const visitedGames = useLocalStorage<Record<string, boolean>>("mitlogic.visited_games", {});

  function booleanFor(flag: string) {
    return computed<boolean>({
      get: () => store.value[flag] ?? true,
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
