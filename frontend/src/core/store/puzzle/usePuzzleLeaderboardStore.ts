import { defineStore } from "pinia";
import { api } from "@/core/services/axios.ts";

interface LeaderboardEntry {
  rank: number;
  duration_display: string;
  username: string;
  is_current_user: boolean;
}

type LeaderboardKey = `${string}:${string}:${string}:${string}`;

export const usePuzzleLeaderboardStore = defineStore("mitlogic.freeplay.leaderboard", {
  state: () => ({
    leaderboard: new Map<LeaderboardKey, LeaderboardEntry[]>(),
  }),

  getters: {
    leaderboardEntryCount:
      (state) =>
      (puzzle_type: string, size: string, difficulty: string, time_period: string = "all_time"): number => {
        const key: LeaderboardKey = `${puzzle_type}:${size}:${difficulty}:${time_period}`;
        if (!state.leaderboard.has(key)) return 0;
        const board: any = state.leaderboard.get(key);
        return board.count;
      },

    getLeaderboard:
      (state) =>
      (puzzle_type: string, size: string, difficulty: string, time_period: string = "all_time"): LeaderboardEntry[] => {
        const key: LeaderboardKey = `${puzzle_type}:${size}:${difficulty}:${time_period}`;
        const board: any = state.leaderboard.get(key);

        return board?.leaderboard || [];
      },
  },

  actions: {
    /** fetch latest leaderboard (Workbox uses NetworkFirst with fallback to cache) */
    async refreshLeaderboard(puzzle_type: string, size: string, difficulty: string, time_period: string = "all_time") {
      try {
        const endpoint = `/api/puzzle/freeplay/leaderboard?puzzle_type=${puzzle_type}&puzzle_size=${size}&puzzle_difficulty=${difficulty}&limit=10&time_period=${time_period}`;
        const response = await api.get(endpoint);
        const data = response.data;
        const key: LeaderboardKey = `${puzzle_type}:${size}:${difficulty}:${time_period}`;
        this.leaderboard.set(key, data);
      } catch (error) {
        return [];
      }
    },
  },
});
