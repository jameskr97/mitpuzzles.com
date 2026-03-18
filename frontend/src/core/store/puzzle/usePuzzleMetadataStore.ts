import { defineStore } from "pinia";
import { api } from "@/core/services/client";

const LOCAL_STORAGE_SELECTED_VARIANT_KEY = (puzzle_type: string) => `mitlogic.${puzzle_type}.selected_variant`;

export const usePuzzleMetadataStore = defineStore("mitlogic.puzzle.metadata", {
  state: () => ({
    variants: {} as Record<string, (string | null)[][]>,
    selected_variant: {} as Record<string, (string | null)[]>,
    initialized: false,
  }),

  getters: {
    getVariants: (state) => (puzzle_type: string): (string | null)[][] => state.variants[puzzle_type] || [],
    getSelectedVariant: (state) => (puzzle_type: string): (string | null)[] => {
        const selected = state.selected_variant[puzzle_type];
        if (selected && selected.length > 0) {
          return selected;
        }
        const variants = state.variants[puzzle_type];
        return variants && variants.length > 0 ? variants[0] : [];
      },
  },

  actions: {
    async initializeStore() {
      if (this.initialized) return;
      this.initialized = true;

      // load from API (Workbox handles caching)
      const { data, error } = await api.GET("/api/puzzle/definition/types");
      if (error) return;
      Object.keys(data).forEach((key) => {
        this.variants[key] = data[key].available_difficulties;
        if (!this.selected_variant[key]) {
          this.selected_variant[key] = data[key].default_difficulty;
        }
      });

      // inject "daily" as the first variant for every puzzle type
      Object.keys(this.variants).forEach((key) => {
        this.variants[key].unshift(["daily"]);
      });

      // load user preferences from localStorage
      this.load_selected_variants();
    },

    set_selected_variant(puzzle_type: string, variant: string[]) {
      this.selected_variant[puzzle_type] = variant;
      try {
        localStorage.setItem(LOCAL_STORAGE_SELECTED_VARIANT_KEY(puzzle_type), JSON.stringify(variant));
      } catch (error) {
        console.warn("Failed to persist selected variant:", error);
        // this is an ok failure. we just won't persist the preference
      }
    },

    load_selected_variants() {
      for (const puzzle_type of Object.keys(this.variants)) {
        try {
          const stored = localStorage.getItem(LOCAL_STORAGE_SELECTED_VARIANT_KEY(puzzle_type));
          if (stored) this.selected_variant[puzzle_type] = JSON.parse(stored);
        } catch (error) {
          console.warn(`Failed to load selected variant for ${puzzle_type}:`, error);
          // this is an ok failure. just set a default.
        }
      }
    },

    doesMatchCurrentVariant(puzzle_type: string, variant: string[]): boolean {
      const current_variant = this.selected_variant[puzzle_type];
      if (!current_variant) return false;
      return current_variant.length === variant.length && current_variant.every((v, i) => v === variant[i]);
    },
  },
});
