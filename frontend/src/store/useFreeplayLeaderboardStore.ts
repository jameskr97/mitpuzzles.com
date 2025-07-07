import { defineStore } from "pinia";
import type { LeaderboardEntry } from "@/store/database/datastores/DatastorePuzzleLeaderboard.ts";
import { getLeaderboard } from "@/services/app";
import { databaseManager } from "@/store/database";

export const useFreeplayLeaderboardStore = defineStore("mitlogic.freeplay.leaderboard", {
  state: () => ({
    leaderboard: new Map<string, LeaderboardEntry[]>(), // string key is "puzzle_type:size:difficulty"
  }),

  getters: {
    leaderboardEntryCount: (state) => (puzzle_type: string, size: string, difficulty: string): number => {
      const key = `${puzzle_type}:${size}:${difficulty}`;
      if (!state.leaderboard.has(key)) {
        console.warn(`Leaderboard for ${key} not found`);
        return 0;
      }
      const board: any = state.leaderboard.get(key);
      return board.count;
    },

    hasLeaderboard: (state) => (puzzle_type: string, size: string, difficulty: string): boolean => {
      const key = `${puzzle_type}:${size}:${difficulty}`;
      return state.leaderboard.has(key);
    },

    getLeaderboard: (state) => (puzzle_type: string, size: string, difficulty: string): LeaderboardEntry[] => {
      const key = `${puzzle_type}:${size}:${difficulty}`;
      console.log(`Fetching leaderboard for ${key}`);
      const board: any = state.leaderboard.get(key);

      return board.leaderboard
    },
  },

  actions: {
    async setLeaderboard(puzzle_type: string, size: string, difficulty: string, leaderboard: LeaderboardEntry[]): Promise<void> {
      const key = `${puzzle_type}:${size}:${difficulty}`;
      this.leaderboard.set(key, leaderboard);

      try {
        await databaseManager.leaderboard.setLeaderboard(puzzle_type, size, difficulty, leaderboard);
      } catch (error) {
        console.warn("Failed to persist leaderboard:", error);
      }
    },

    async getOrFetchLeaderboard(puzzle_type: string, size: string, difficulty: string): Promise<LeaderboardEntry[]> {
      if (this.hasLeaderboard(puzzle_type, size, difficulty)) {
        return this.getLeaderboard(puzzle_type, size, difficulty);
      }
      return await this.refreshLeaderboard(puzzle_type, size, difficulty);
    },

    async refreshLeaderboard(puzzle_type: string, size: string, difficulty: string): Promise<LeaderboardEntry[]> {
      try {
        const data = await getLeaderboard(puzzle_type, size, difficulty);
        await this.setLeaderboard(puzzle_type, size, difficulty, data.data);
        return data.leaderboard;
      } catch (error) {
        console.error("Failed to refresh leaderboard:", error);
        return [];
      }
    },

    async loadLeaderboardFromCache(puzzle_type: string, size: string, difficulty: string): Promise<LeaderboardEntry[]> {
      try {
        const cachedLeaderboard = await databaseManager.leaderboard.loadLeaderboard(puzzle_type, size, difficulty);
        if (cachedLeaderboard.length > 0) {
          const key = `${puzzle_type}:${size}:${difficulty}`;
          this.leaderboard.set(key, cachedLeaderboard);
        }
        return cachedLeaderboard;
      } catch (error) {
        console.warn("Failed to load leaderboard from cache:", error);
        return [];
      }
    },


  },
});
