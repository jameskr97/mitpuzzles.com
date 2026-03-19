import { defineStore } from "pinia";
import { api } from "@/core/services/client";
import { capture_error } from "@/core/services/posthog.ts";
import type { DailyPuzzleStatus, LeaderboardEntry } from "@/core/types";

type LeaderboardKey = `${string}:${string}`;

export const useDailyPuzzleStore = defineStore("mitlogic.daily", {
  state: () => ({
    today_date: "" as string,
    puzzles: [] as DailyPuzzleStatus[],
    leaderboards: {} as Record<LeaderboardKey, LeaderboardEntry[]>,
    loading: false,
  }),

  getters: {
    getDailyLeaderboard: (state) => (date: string, puzzle_type: string): LeaderboardEntry[] => {
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
      const { data, error } = await api.GET("/api/puzzle/daily/today");
      this.loading = false;

      if (error) {
        capture_error("daily_puzzles_fetch_failed", error);
        return;
      }

      this.today_date = data.date;
      this.puzzles = data.puzzles;
    },

    /** fetch only if the stored date is stale */
    async ensureFresh() {
      if (this.isStale()) {
        await this.fetchDailyPuzzles();
      }
    },

    async fetchDailyDefinition(date: string, puzzle_type: string) {
      const { data, error } = await api.GET("/api/puzzle/daily/{date}/definition/{puzzle_type}", {
        params: { path: { date, puzzle_type } },
      });
      if (error) return null;
      return data;
    },

    async refreshDailyLeaderboard(date: string, puzzle_type: string) {
      const { data, error } = await api.GET("/api/puzzle/daily/{date}/leaderboard/{puzzle_type}", {
        params: { path: { date, puzzle_type } },
      });
      if (error) return;
      const key: LeaderboardKey = `${date}:${puzzle_type}`;
      this.leaderboards[key] = data.leaderboard || [];
    },

    async submitDailyAttempt(date: string, puzzle_type: string, attempt_data: any) {
      const { data, error } = await api.POST("/api/puzzle/daily/{date}/submit/{puzzle_type}", {
        params: { path: { date, puzzle_type } },
        body: attempt_data,
      });
      if (error) {
        capture_error("daily_submit_failed", error, { date, puzzle_type });
        return null;
      }
      return data;
    },
  },
});
