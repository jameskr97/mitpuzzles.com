/**
 * daily puzzle store.
 *
 * - fetches today's daily puzzle info
 * - saves it into puzzle stores using "daily" as puzzle_type key
 * - clears progress when date changes.
 */

import { defineStore } from "pinia";
import { api } from "@/core/services/client";
import { usePuzzleProgressStore } from "@/core/store/puzzle/usePuzzleProgressStore";
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

// @ts-ignore
export const useDailyPuzzleStore = defineStore("puzzle.daily", {
  state: () => ({
    daily: null as DailyTodayResponse | null,
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
    definition: () => usePuzzleProgressStore().get_definition(DAILY_KEY),
    preview_state() {
      const def = this.definition;
      // @ts-expect-error ts compiler can't tell that this.definition is called by pinia so we don't call it.
      return def ? { definition: def, board: def.initial_state } : null;
    },
    solved_state(): PuzzleDefinition | null {
      const board = this.daily?.puzzle.board_state;
      if (!board || !this.daily?.puzzle.is_solved || !this.definition) return null;
      return {
        // @ts-expect-error ts compiler can't tell that this.definition is called by pinia so we don't call it.
        definition: this.definition,
        board,
      };
    },
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
        const progress_store = usePuzzleProgressStore();
        const stored_date = localStorage.getItem(DAILY_DATE_KEY);
        const current_id = progress_store.get_puzzle_id(DAILY_KEY);

        if (stored_date !== data.date || current_id !== data.puzzle.puzzle_id) {
          emitter.emit("daily:clear-progress", { key: DAILY_KEY });
        }

        localStorage.setItem(DAILY_DATE_KEY, data.date);

        this.daily = data;

        // fetch the full puzzle definition
        const { data: def_data } = await api.GET("/api/puzzle/definition/{puzzle_id}", {
          params: { path: { puzzle_id: data.puzzle.puzzle_id } },
        });
        if (def_data) {
          progress_store.set_definition(DAILY_KEY, def_data as PuzzleDefinition);
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

    async claimForUser() {
      const { data, error } = await api.POST("/api/puzzle/daily/claim");
      if (error) return false;
      if (data.claimed) {
        await this.refreshLeaderboard();
      }
      return data.claimed;
    },

    async refresh() {
      this.initialized = false;
      this.daily = null;
      this.leaderboard = [];
      await this.init();
    },

  },
});
