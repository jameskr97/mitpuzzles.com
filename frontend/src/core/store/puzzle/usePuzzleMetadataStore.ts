import { defineStore } from "pinia";
import { api } from "@/core/services/client";
import type { PuzzleVariant } from "@/core/types";

export const DAILY_VARIANT: PuzzleVariant = { size: "daily", difficulty: null };

const LOCAL_STORAGE_SELECTED_VARIANT_KEY = (puzzle_type: string) => `mitlogic.${puzzle_type}.selected_variant`;

export const usePuzzleMetadataStore = defineStore("mitlogic.puzzle.metadata", {
  state: () => ({
    variants: {} as Record<string, PuzzleVariant[]>,
    selected_variant: {} as Record<string, PuzzleVariant>,
    initialized: false,
  }),

  getters: {
    getVariants: (state) => (puzzle_type: string): PuzzleVariant[] => state.variants[puzzle_type] || [],
    getSelectedVariant: (state) => (puzzle_type: string): PuzzleVariant => {
        const selected = state.selected_variant[puzzle_type];
        if (selected) return selected;
        const variants = state.variants[puzzle_type];
        return variants && variants.length > 0 ? variants[0] : DAILY_VARIANT;
      },
  },

  actions: {
    async initializeStore() {
      if (this.initialized) return;
      this.initialized = true;

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
        this.variants[key].unshift(DAILY_VARIANT);
      });

      this.load_selected_variants();
    },

    set_selected_variant(puzzle_type: string, variant: PuzzleVariant) {
      this.selected_variant[puzzle_type] = variant;
      try {
        localStorage.setItem(LOCAL_STORAGE_SELECTED_VARIANT_KEY(puzzle_type), JSON.stringify(variant));
      } catch (error) {
        console.warn("Failed to persist selected variant:", error);
      }
    },

    load_selected_variants() {
      for (const puzzle_type of Object.keys(this.variants)) {
        try {
          const stored = localStorage.getItem(LOCAL_STORAGE_SELECTED_VARIANT_KEY(puzzle_type));
          if (stored) this.selected_variant[puzzle_type] = JSON.parse(stored);
        } catch (error) {
          console.warn(`Failed to load selected variant for ${puzzle_type}:`, error);
        }
      }
    },

    doesMatchCurrentVariant(puzzle_type: string, variant: PuzzleVariant): boolean {
      const current = this.selected_variant[puzzle_type];
      if (!current) return false;
      return current.size === variant.size && current.difficulty === variant.difficulty;
    },
  },
});
