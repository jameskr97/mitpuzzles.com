import { defineStore } from "pinia";
import { api } from "@/core/services/client";
import type { LeaderboardEntry, LeaderboardResponse } from "@/core/types";

type LeaderboardKey = `${string}:${string}:${string}:${string}:${string}`;

export const usePuzzleLeaderboardStore = defineStore("mitlogic.freeplay.leaderboard", {
  state: () => ({
    leaderboard: {} as Record<LeaderboardKey, LeaderboardResponse>,
  }),

  getters: {
    leaderboardEntryCount:
      (state) =>
      (puzzle_type: string, size: string, difficulty: string, time_period: string = "all_time", scoring_method: string = "best"): number => {
        const key: LeaderboardKey = `${puzzle_type}:${size}:${difficulty}:${time_period}:${scoring_method}`;
        return state.leaderboard[key]?.count ?? 0;
      },

    getLeaderboard:
      (state) =>
      (puzzle_type: string, size: string, difficulty: string, time_period: string = "all_time", scoring_method: string = "best"): LeaderboardEntry[] => {
        const key: LeaderboardKey = `${puzzle_type}:${size}:${difficulty}:${time_period}:${scoring_method}`;
        return state.leaderboard[key]?.leaderboard ?? [];
      },
  },

  actions: {
    /** fetch latest leaderboard (Workbox uses NetworkFirst with fallback to cache) */
    async refreshLeaderboard(puzzle_type: string, size: string, difficulty: string, time_period: string = "all_time", scoring_method: string = "best") {
      const { data, error } = await api.GET("/api/puzzle/freeplay/leaderboard", {
        params: { query: { puzzle_type, puzzle_size: size, puzzle_difficulty: difficulty, limit: 10, time_period, scoring_method } },
      });
      if (error) return;
      const key: LeaderboardKey = `${puzzle_type}:${size}:${difficulty}:${time_period}:${scoring_method}`;
      this.leaderboard[key] = data;
    },
  },
});
