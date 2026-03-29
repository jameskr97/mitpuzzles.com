/**
 * daily puzzle store.
 *
 * - fetches today's daily puzzle info
 * - saves it into puzzle stores using "daily" as puzzle_type key
 * - clears progress when date changes.
 */

import { defineStore } from "pinia";
import { api } from "@/core/services/client";
import { setCurrentPuzzleID, getCurrentPuzzleID } from "@/core/store/puzzle/usePuzzleDefinitionStore";
import { usePuzzleProgressStore } from "@/core/store/puzzle/usePuzzleProgressStore";
import { usePuzzleHistoryStore } from "@/core/store/puzzle/usePuzzleHistoryStore";
import { databaseManager } from "@/core/store/database";
import { ACTIVE_GAMES } from "@/constants";
import type { PuzzleDefinition } from "@/core/games/types/puzzle-types";
import type { LeaderboardEntry } from "@/core/types";

const DAILY_KEY = "daily";
const DAILY_DATE_KEY = "mitlogic.daily_date";

export interface DailyPuzzleInfo {
  date: string;
  puzzle_type: string;
  puzzle_size: string;
  puzzle_difficulty: string | null;
  puzzle_id: string;
  daily_puzzle_id: string;
  is_solved: boolean;
  completion_time: string | null;
}

export const useDailyPuzzleStore = defineStore("puzzle.daily", {
  state: () => ({
    daily: null as DailyPuzzleInfo | null,
    definition: null as PuzzleDefinition | null,
    leaderboard: [] as LeaderboardEntry[],
    loading: false,
    error: null as string | null,
    initialized: false,
  }),

  getters: {
    is_ready: (state) => state.daily !== null,
    puzzle_type: (state) => state.daily?.puzzle_type ?? null,
    game_entry: (state) => state.daily ? ACTIVE_GAMES[state.daily.puzzle_type] ?? null : null,
    component: (state) => state.daily ? ACTIVE_GAMES[state.daily.puzzle_type]?.component ?? null : null,
    preview_state: (state) => state.definition ? { definition: state.definition, board: state.definition.initial_state } : null,
  },

  actions: {
    async init() {
      if (this.initialized) return;
      this.initialized = true;
      await this.fetch();
    },

    async fetch() {
      this.loading = true;
      this.error = null;

      try {
        const { data, error } = await api.GET("/api/puzzle/daily/today");
        if (error || !data) {
          this.error = "failed to fetch daily puzzle";
          return;
        }

        const puzzle = data.puzzle;
        const info: DailyPuzzleInfo = {
          date: data.date,
          puzzle_type: puzzle.puzzle_type,
          puzzle_size: puzzle.puzzle_size,
          puzzle_difficulty: puzzle.puzzle_difficulty ?? null,
          puzzle_id: puzzle.puzzle_id,
          daily_puzzle_id: puzzle.daily_puzzle_id,
          is_solved: puzzle.is_solved,
          completion_time: puzzle.completion_time ?? null,
        };

        // check if the date or puzzle changed — clear old progress
        const stored_date = localStorage.getItem(DAILY_DATE_KEY);
        const current_id = getCurrentPuzzleID(DAILY_KEY);

        if (stored_date !== info.date || current_id !== info.puzzle_id) {
          const progress_store = usePuzzleProgressStore();
          await progress_store.init();
          delete progress_store.timestamp_start[DAILY_KEY];
          delete progress_store.timestamp_finish[DAILY_KEY];
          delete progress_store.current_puzzle_states[DAILY_KEY];
          delete progress_store.used_tutorial[DAILY_KEY];
          await databaseManager.progress.delete(DAILY_KEY);

          const history_store = usePuzzleHistoryStore();
          await history_store.init();
          await history_store.clear_events(DAILY_KEY, "freeplay");
        }

        // set puzzle ID so useFreeplayServices("daily") picks it up
        setCurrentPuzzleID(DAILY_KEY, info.puzzle_id);
        localStorage.setItem(DAILY_DATE_KEY, info.date);

        this.daily = info;

        // fetch the full puzzle definition
        const { data: def_data } = await api.GET("/api/puzzle/definition/{puzzle_id}", {
          params: { path: { puzzle_id: info.puzzle_id } },
        });
        if (def_data) {
          this.definition = def_data as PuzzleDefinition;
        }
      } catch (e) {
        this.error = "failed to fetch daily puzzle";
      } finally {
        this.loading = false;
      }
    },

    async refreshLeaderboard() {
      if (!this.daily) return;
      const { data } = await api.GET("/api/puzzle/daily/{date}/leaderboard", {
        params: { path: { date: this.daily.date } },
      });
      if (data) {
        this.leaderboard = data.leaderboard as LeaderboardEntry[];
      }
    },

    async refresh() {
      this.initialized = false;
      this.daily = null;
      this.definition = null;
      this.leaderboard = [];
      await this.init();
    },
  },
});
