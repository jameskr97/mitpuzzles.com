import { remap } from "@/services/util";
import { defineStore } from "pinia";
import { computed } from "vue";
import { useRoute } from "vue-router";
import { useLocalStorage } from "@vueuse/core";
import { ACTIVE_GAMES } from "@/constants.ts";

/**
 * Each game will have its own scale value, and we store that in local storage,
 * and in a dictionary.
 */
const useScaleStore = defineStore("mitlogic.scale", () => {
  const scales = useLocalStorage<Record<string, number>>("mitlogic.scale", {});

  // t = type, v = variant
  const key = (t: string, v: string) => `${t}:${v}`;

  /** returns a computed<number> that you can read *and* write */
  function scaleFor(type: string, variant = "default") {
    return computed<number[]>({
      get: () => [scales.value[key(type, variant)] ?? [20]],
      set: (v: number[]) => (scales.value[key(type, variant)] = v[0]),
    });
  }
  return { scaleFor };
});

export function getGameScale(): any {
  // Get the current route and store
  const route = useRoute();
  const store = useScaleStore();

  // Create user-accessible scale properties
  const scale = store.scaleFor(game_type);
  const scale_remapped = computed(() => remap([0, 100], [1, 6], scale.value[0]));
  return { scale, scale_remapped };
}
