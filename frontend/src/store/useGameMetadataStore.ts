import { defineStore } from "pinia";
import { getPuzzleTypes } from "@/services/app.ts";
import { databaseManager } from "@/store/database";

// Configuration
export const CACHE_VERSION = 1; // Increment to invalidate metadata cache

export const useGameMetadataStore = defineStore("mitlogic.puzzle.metadata", {
  state: () => ({
    variants: {} as Record<string, string[][]>,
    selected_variant: {} as Record<string, string[]>,
    initialized: false,
    cacheValid: false,
  }),

  getters: {
    getVariants:
      (state) =>
      (puzzle_type: string): string[][] =>
        state.variants[puzzle_type] || [],

    getSelectedVariant:
      (state) =>
      (puzzle_type: string): string[] => {
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

      try {
        // Initialize database manager
        await databaseManager.init();

        // Check if cache is valid
        const storedVersion = await databaseManager.cache.getCacheVersion();
        this.cacheValid = storedVersion === CACHE_VERSION;

        if (this.cacheValid) {
          console.log("Loading puzzle metadata from cache");
          const allData = await databaseManager.metadata.getAllMetadata();

          for (const item of allData) {
            this.variants[item.id] = item.variants;
            this.selected_variant[item.id] = item.selected_variant || item.variants[0] || [];
          }
        } else {
          console.log("Cache version mismatch, will refresh data");
          await this.refreshAllVariants();
          await databaseManager.cache.setCacheVersion(CACHE_VERSION);
          this.cacheValid = true;
        }

        this.initialized = true;
      } catch (error) {
        console.error("Failed to initialize puzzle metadata store:", error);
        this.initialized = true;
      }
    },

    async setSelectedVariant(puzzle_type: string, variant: string[]) {
      this.selected_variant[puzzle_type] = variant;

      try {
        await databaseManager.metadata.setMetadata(puzzle_type, {
          variants: this.variants[puzzle_type] || [],
          selected_variant: variant,
          cacheVersion: CACHE_VERSION,
        });
      } catch (error) {
        console.warn("Failed to persist selected variant:", error);
      }
    },

    doesMatchCurrentVariant(puzzle_type: string, variant: string[]): boolean {
      const current_variant = this.selected_variant[puzzle_type];
      if (!current_variant) return false;
      return current_variant.length === variant.length && current_variant.every((v, i) => v === variant[i]);
    },

    async refreshAllVariants(): Promise<void> {
      console.log("Refreshing all puzzle variants from server");

      try {
        const response = await getPuzzleTypes();
        const PUZZLE_METADATA = response.data;

        for (const puzzle_type of Object.keys(PUZZLE_METADATA)) {
          const puzzle_data = PUZZLE_METADATA[puzzle_type];
          if (!puzzle_data) {
            console.warn(`No data found for puzzle type: ${puzzle_type}`);
            continue;
          }

          this.variants[puzzle_type] = puzzle_data.available_difficulties;

          // Always ensure we have a selected variant
          if (!this.selected_variant[puzzle_type] || this.selected_variant[puzzle_type].length === 0) {
            this.selected_variant[puzzle_type] = puzzle_data.default_difficulty;
          }

          await databaseManager.metadata.setMetadata(puzzle_type, {
            variants: puzzle_data.available_difficulties,
            selected_variant: this.selected_variant[puzzle_type],
            cacheVersion: CACHE_VERSION,
          });
        }
      } catch (error) {
        console.error("Failed to fetch puzzle variants:", error);
      }
    },

    async invalidateCache(): Promise<void> {
      await databaseManager.metadata.clearMetadata();
      await databaseManager.cache.setCacheVersion(0);
      this.variants = {};
      this.selected_variant = {};
      this.cacheValid = false;
      console.log("Metadata cache manually invalidated");
    },
  },
});
