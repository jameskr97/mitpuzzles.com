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
import { ACTIVE_GAMES } from "@/constants";
import type { PuzzleDefinition } from "@/core/games/types/puzzle-types";
import type { DailyTodayResponse, LeaderboardEntry } from "@/core/types";
import { emitter } from "@/core/services/event-bus.ts";

emitter.on("puzzle:solved:daily", async () => {
  const store = useDailyPuzzleStore();
  await store.refreshLeaderboard();
});

const DAILY_KEY = "daily";
const DAILY_DATE_KEY = "mitlogic.daily_date";

export const useDailyPuzzleStore = defineStore("puzzle.daily", {
  state: () => ({
    daily: null as DailyTodayResponse | null,
    definition: null as PuzzleDefinition | null,
    leaderboard: [] as LeaderboardEntry[],
    loading: false,
    error: null as string | null,
    initialized: false,
  }),

  getters: {
    is_ready: (state) => state.daily !== null,
    puzzle_type: (state) => state.daily?.puzzle.puzzle_type ?? null,
    game_entry: (state) => state.daily ? ACTIVE_GAMES[state.daily.puzzle.puzzle_type] ?? null : null,
    component: (state) => state.daily ? ACTIVE_GAMES[state.daily.puzzle.puzzle_type]?.component ?? null : null,
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

        // check if the date or puzzle changed — clear old progress
        const stored_date = localStorage.getItem(DAILY_DATE_KEY);
        const current_id = getCurrentPuzzleID(DAILY_KEY);

        if (stored_date !== data.date || current_id !== data.puzzle.puzzle_id) {
          emitter.emit("daily:clear-progress", { key: DAILY_KEY });
        }

        // set puzzle ID so useFreeplayServices("daily") picks it up
        setCurrentPuzzleID(DAILY_KEY, data.puzzle.puzzle_id);
        localStorage.setItem(DAILY_DATE_KEY, data.date);

        this.daily = data;

        // fetch the full puzzle definition
        const { data: def_data } = await api.GET("/api/puzzle/definition/{puzzle_id}", {
          params: { path: { puzzle_id: data.puzzle.puzzle_id } },
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
      const { data, error } = await api.GET("/api/puzzle/daily/{date}/leaderboard", {
        params: { path: { date: this.daily.date } },
      });
      if (error) throw Error("Could not fetch leaderboard");

      this.leaderboard = data.leaderboard as LeaderboardEntry[];
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
