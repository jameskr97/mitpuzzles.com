import { defineStore } from "pinia";
import { useLocalStorage } from "@vueuse/core";
import { computed } from "vue";

export function useGameLayout() {
  const store = useGameLayoutStore();

  const instructions_visible = store.booleanFor("instructions");
  const leaderboard_visible = store.booleanFor("leaderboard");

  return {
    instructions_visible,
    leaderboard_visible,
    toggle_instructions: () => (instructions_visible.value = !instructions_visible.value),
    toggle_leaderboard: () => (leaderboard_visible.value = !leaderboard_visible.value),
  };
}

export const useGameLayoutStore = defineStore("mitlogic.layout", () => {
  const store = useLocalStorage<Record<string, boolean>>("mitlogic.gamelayout", {});

  function booleanFor(flag: string) {
    return computed<boolean>({
      get: () => store.value[flag] ?? true,
      set: (v) => (store.value[flag] = v),
    });
  }

  return { booleanFor };
});
