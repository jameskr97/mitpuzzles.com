import { defineStore } from "pinia";
import { shared_http_cache } from "@/store/database/HTTPCache.ts";

interface LeaderboardEntry {
  rank: number;
  duration_display: string;
  username: string;
}

type LeaderboardKey = `${string}:${string}:${string}`;

export const usePuzzleLeaderboardStore = defineStore("mitlogic.freeplay.leaderboard", {
  state: () => ({
    leaderboard: new Map<LeaderboardKey, LeaderboardEntry[]>(),
  }),

  getters: {
    leaderboardEntryCount:
      (state) =>
      (puzzle_type: string, size: string, difficulty: string): number => {
        const key: LeaderboardKey = `${puzzle_type}:${size}:${difficulty}`;
        if (!state.leaderboard.has(key)) return 0;
        const board: any = state.leaderboard.get(key);
        return board.count;
      },

    getLeaderboard:
      (state) =>
      (puzzle_type: string, size: string, difficulty: string): LeaderboardEntry[] => {
        const key: LeaderboardKey = `${puzzle_type}:${size}:${difficulty}`;
        const board: any = state.leaderboard.get(key);

        return board?.leaderboard || [];
      },
  },

  actions: {
    /** not really caching, because we only call .refresh, but that's fine for now */
    async refreshLeaderboard(puzzle_type: string, size: string, difficulty: string) {
      try {
        const endpoint = `/api/puzzle/freeplay/leaderboard?puzzle_type=${puzzle_type}&puzzle_size=${size}&puzzle_difficulty=${difficulty}&limit=10`;
        const data = await shared_http_cache.refresh(endpoint)
        const key: LeaderboardKey = `${puzzle_type}:${size}:${difficulty}`;
        this.leaderboard.set(key, data);
      } catch (error) {
        return [];
      }
    },
  },
});
