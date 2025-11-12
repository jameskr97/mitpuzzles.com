import { defineStore } from "pinia";
import { api } from "@/services/axios.ts";

const LOCAL_STORAGE_SELECTED_VARIANT_KEY = (puzzle_type: string) => `mitlogic.${puzzle_type}.selected_variant`;

export const usePuzzleMetadataStore = defineStore("mitlogic.puzzle.metadata", {
  state: () => ({
    variants: {} as Record<string, string[][]>, // puzzle_type -> list of variants (each variant is a list of strings)
    selected_variant: {} as Record<string, string[]>,
    initialized: false,
  }),

  getters: {
    getVariants: (state) => (puzzle_type: string): string[][] => state.variants[puzzle_type] || [],
    getSelectedVariant: (state) => (puzzle_type: string): string[] => {
        const selected = state.selected_variant[puzzle_type];
        if (selected && selected.length > 0) {
          return selected;
        }
        // Fallback to first variant if no selection or empty selection
        const variants = state.variants[puzzle_type];
        return variants && variants.length > 0 ? variants[0] : [];
      },
  },

  actions: {
    async initializeStore() {
      if (this.initialized) return;
      this.initialized = true;

      // load from API (Workbox handles caching)
      const response = await api.get('/api/puzzle/definition/types');
      const loaded = response.data;
      Object.keys(loaded).forEach((key) => {
        this.variants[key] = loaded[key].available_difficulties;
        // set default if no selection exists
        if (!this.selected_variant[key]) {
          this.selected_variant[key] = loaded[key].default_difficulty;
        }
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
