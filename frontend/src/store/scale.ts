import { remap } from "@/lib/util";
import { defineStore } from "pinia";
import { computed } from "vue";
import { useRoute } from "vue-router";
import { useLocalStorage } from "@vueuse/core";

/**
 * Each game will have it's own scale value, and we store that in local storage,
 * and in a dictionary.
 */
const useScaleStore = defineStore("mitlogic.scale", () => {
  const scales = useLocalStorage<Record<string, number>>("mitlogic.scale", {});

  // t = type, v = variant
  const key = (t: string, v: string) => `${t}:${v}`;

  /** returns a computed<number> that you can read *and* write */
  function scaleFor(type: string, variant = "default") {
    return computed<number>({
      get: () => scales.value[key(type, variant)] ?? 20,
      set: (v) => (scales.value[key(type, variant)] = v),
    });
  }
  return { scaleFor };
});

export function getGameScale(): any {
  // Get the current route and store
  const route = useRoute();
  const store = useScaleStore();

  // Get the game type from the route meta
  const game_type = route.meta.game_type as string;

  // Create user-accessible scale properties
  const scale = store.scaleFor(game_type);
  const scale_remapped = computed(() => remap([0, 100], [2, 6], scale.value));
  return { scale, scale_remapped };
}
