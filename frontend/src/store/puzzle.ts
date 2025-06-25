import { defineStore } from "pinia";
import { useLocalStorage } from "@vueuse/core";
import { getPuzzleVariants } from "@/services/app.ts";
import { ACTIVE_GAMES } from "@/constants.ts";

export const usePuzzleMetadataStore = defineStore("mitlogic.puzzle.metadata", {
  state: () => ({
    variants: useLocalStorage("mitlogic.puzzle.variants", {} as Record<string, string[][]>),
    selected_variant: useLocalStorage("mitlogic.puzzle.variants.selected", {} as Record<string, string[]>),
    last_updated: useLocalStorage("mitlogic.puzzle.variants.updated", 0),
  }),
  getters: {
    getVariants:        (state) => (puzzle_type: string): string[][]  => state.variants[puzzle_type] || [],
    getSelectedVariant: (state) => (puzzle_type: string): string[]    => state.selected_variant[puzzle_type]
  },

  actions: {
    setSelectedVariant(puzzle_type: string, variant: string[]) {
      this.selected_variant[puzzle_type] = variant;
    },
    doesMatchCurrentVariant(puzzle_type: string, variant: string[]): boolean {
      const current_variant = this.selected_variant[puzzle_type];
      if (!current_variant) return false;
      return current_variant.length === variant.length && current_variant.every((v, i) => v === variant[i]);
    },
    async refreshAllVariantsOnce() {
      const STALE_THRESHOLD = (3600 * 24) * 1000; // 24 hours in milliseconds
      const now = Date.now();

      if (now - this.last_updated > STALE_THRESHOLD) {
        for (const puzzle_type of Object.keys(ACTIVE_GAMES)) {
          const response = await getPuzzleVariants(puzzle_type);
          this.variants[puzzle_type] = response.data;

          if (!this.selected_variant[puzzle_type]) {
            this.selected_variant[puzzle_type] = response.data[0];
          }
        }
        this.last_updated = now;
      }
    },
  },
});
