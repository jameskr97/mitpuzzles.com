import { defineStore } from "pinia";
import { api } from "@/core/services/axios.ts";
import { capture_error } from "@/core/services/posthog.ts";

export interface DailyPuzzleStatus {
  puzzle_type: string;
  puzzle_id: string;
  daily_puzzle_id: string;
  is_solved: boolean;
  completion_time: string | null;
}

export interface DailyLeaderboardEntry {
  rank: number;
  duration_display: string;
  username: string;
  is_current_user: boolean;
}

type LeaderboardKey = `${string}:${string}`;

export const useDailyPuzzleStore = defineStore("mitlogic.daily", {
  state: () => ({
    today_date: "" as string,
    puzzles: [] as DailyPuzzleStatus[],
    leaderboards: {} as Record<LeaderboardKey, DailyLeaderboardEntry[]>,
    loading: false,
  }),

  getters: {
    getDailyLeaderboard: (state) => (date: string, puzzle_type: string): DailyLeaderboardEntry[] => {
      const key: LeaderboardKey = `${date}:${puzzle_type}`;
      return state.leaderboards[key] || [];
    },
  },

  actions: {
    /** Returns true if the stored date is stale (not today) */
    isStale(): boolean {
      if (!this.today_date) return true;
      const now = new Date();
      const today = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
      return this.today_date !== today;
    },

    async fetchDailyPuzzles() {
      this.loading = true;
      try {
        const response = await api.get("/api/puzzle/daily/today");
        this.today_date = response.data.date;
        this.puzzles = response.data.puzzles;
      } catch (error) {
        capture_error("daily_puzzles_fetch_failed", error);
      } finally {
        this.loading = false;
      }
    },

    /** Fetch only if the stored date is stale */
    async ensureFresh() {
      if (this.isStale()) {
        await this.fetchDailyPuzzles();
      }
    },

    async fetchDailyDefinition(date: string, puzzle_type: string) {
      const response = await api.get(`/api/puzzle/daily/${date}/definition/${puzzle_type}`);
      return response.data;
    },

    async refreshDailyLeaderboard(date: string, puzzle_type: string) {
      try {
        const response = await api.get(`/api/puzzle/daily/${date}/leaderboard/${puzzle_type}`);
        const key: LeaderboardKey = `${date}:${puzzle_type}`;
        this.leaderboards[key] = response.data.leaderboard || [];
      } catch {
        // keep existing data on error
      }
    },

    async submitDailyAttempt(date: string, puzzle_type: string, attempt_data: any) {
      const response = await api.post(`/api/puzzle/daily/${date}/submit/${puzzle_type}`, attempt_data);
      return response.data;
    },
  },
});
