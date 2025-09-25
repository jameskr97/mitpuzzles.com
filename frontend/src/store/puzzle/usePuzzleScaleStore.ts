import { defineStore } from "pinia";
import { remap } from "@/services/util.ts";
import { ACTIVE_GAMES } from "@/constants.ts";

const STORAGE_KEY = 'mitlogic.puzzle.scales';

export const usePuzzleScaleStore = defineStore("puzzle.scale", {
  state: () => ({
    scales: {} as Record<string, number>,
    DEFAULT_SCALE: 10,
  }),

  getters: {
    getScale: (state) => (puzzle_type: string): number => state.scales[puzzle_type] ?? state.DEFAULT_SCALE,
    getScaleRemapped: (state) => (puzzle_type: string): number => remap([0, 100], [1, 6], state.scales[puzzle_type]),
  },

  actions: {
    init() {
      const stored = localStorage.getItem(STORAGE_KEY);
      this.scales = stored ? JSON.parse(stored) : {};

      for (const puzzle_type of Object.keys(ACTIVE_GAMES)) {
        if (!this.scales[puzzle_type]) {
          this.scales[puzzle_type] = this.DEFAULT_SCALE;
        }
      }
    },

    setScale(puzzle_type: string, scale: number): void {
      this.scales[puzzle_type] = scale;
      localStorage.setItem(STORAGE_KEY, JSON.stringify(this.scales));
    },
  },
});
