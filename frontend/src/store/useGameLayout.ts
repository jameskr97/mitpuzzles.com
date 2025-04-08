import { useLocalStorage } from "@vueuse/core";
import { defineStore } from "pinia";
import { computed } from "vue";

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
