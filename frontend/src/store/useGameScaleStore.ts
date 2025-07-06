import { defineStore } from "pinia";
import { remap } from "@/services/util.ts";
import { ACTIVE_GAMES } from "@/constants.ts";
import { databaseManager } from "@/store/database";

export const useGameScalesStore = defineStore("game.scales", {
  state: () => ({
    initialized: false,
    scales: {} as Record<string, number>,
    DEFAULT_SCALE: 10,
  }),

  getters: {
    getScale:
      (state) =>
      (puzzle_type: string): number => {
        return state.scales[puzzle_type] || state.DEFAULT_SCALE;
      },
    getScaleRemapped:
      (state) =>
      (puzzle_type: string): number =>
        remap([0, 100], [1, 6], state.scales[puzzle_type]),
  },

  actions: {
    async initializeStore() {
      if (this.initialized) return;

      try {
        await databaseManager.init();

        // Load all scales
        this.scales = await databaseManager.scales.getAllScales();

        // Initialize missing puzzle types
        for (const puzzle_type of Object.keys(ACTIVE_GAMES)) {
          if (!this.scales[puzzle_type]) {
            await databaseManager.scales.setScale(puzzle_type, this.DEFAULT_SCALE);
            this.scales[puzzle_type] = this.DEFAULT_SCALE;
          }
        }

        this.initialized = true;
      } catch (error) {
        console.error("Failed to initialize puzzle scales store:", error);
        this.initialized = false;
      }
    },

    async setScale(puzzle_type: string, scale: number): Promise<void> {
      this.scales[puzzle_type] = scale;

      try {
        await databaseManager.scales.setScale(puzzle_type, scale);
      } catch (error) {
        console.warn(`Failed to persist scale for ${puzzle_type}:`, error);
      }
    },
  },
});
