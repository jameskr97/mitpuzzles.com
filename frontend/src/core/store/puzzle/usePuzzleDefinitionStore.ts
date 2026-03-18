import { defineStore } from "pinia";
import type { PuzzleDefinition } from "@/core/games/types/puzzle-types.ts";
import { useSessionTrackingStore } from "@/core/store/useSessionTrackingStore.ts";
import { api } from "@/core/services/client";
import { capture_error } from "@/core/services/posthog.ts";

// localStorage helpers
export function getCurrentPuzzleID(puzzle_type: string): string | null {
  return localStorage.getItem(`mitlogic.${puzzle_type}.current_id`);
}

function setCurrentPuzzleId(puzzle_type: string, puzzle_id: string): void {
  localStorage.setItem(`mitlogic.${puzzle_type}.current_id`, puzzle_id);
}

export const usePuzzleDefinitionStore = defineStore("puzzle-definitions", {

  actions: {
    /** set current puzzle for a type (stores puzzle_type -> puzzle_id mapping) */
    setCurrentPuzzle: (puzzle_type: string, puzzle_id: string): void => setCurrentPuzzleId(puzzle_type, puzzle_id),

    /** get puzzle definition by puzzle type (uses current puzzle ID from localStorage) */
    async getDefinition(puzzle_type: string): Promise<PuzzleDefinition | null> {
      const puzzle_id = getCurrentPuzzleID(puzzle_type);
      if (!puzzle_id) return null;
      return await this.getDefinitionByID(puzzle_id);
    },

    /** get puzzle definition by specific puzzle ID (Workbox handles caching) */
    async getDefinitionByID(puzzle_id: string): Promise<PuzzleDefinition | null> {
      const { data, error } = await api.GET("/api/puzzle/definition/{puzzle_id}", {
        params: { path: { puzzle_id } },
      });
      if (error) {
        console.warn(`Failed to get puzzle definition for ID ${puzzle_id}:`, error.detail);
        return null;
      }
      return (data as PuzzleDefinition) ?? null;
    },

    /** request a new puzzle from the server and set it as current */
    async requestNewPuzzle<TMeta>(puzzle_type: string, size: string, difficulty: string): Promise<PuzzleDefinition<TMeta> | null> {
      const sessionStore = useSessionTrackingStore();

      // request 1: get next puzzle id (with priority and uniqueness enforcement)
      const { data: idData, error } = await api.GET("/api/puzzle/next", {
        params: { query: { puzzle_type, puzzle_size: size, puzzle_difficulty: difficulty, session_id: sessionStore.session_id } },
      });
      if (error) {
        capture_error("next_puzzle_failed", error, { puzzle_type, size, difficulty });
        return null;
      }

      const puzzle_id = idData.puzzle_id;
      this.setCurrentPuzzle(puzzle_type, puzzle_id);

      // request 2: get puzzle definition by id (Workbox caches it)
      const definition = await this.getDefinitionByID(puzzle_id);
      if (!definition) {
        capture_error("puzzle_definition_failed", null, { puzzle_id });
        return null;
      }

      return definition as PuzzleDefinition<TMeta>;
    },

    /** get existing puzzle or fetch a new one */
    async getOrFetchPuzzle<TMeta>(puzzle_type: string, size: string, difficulty: string): Promise<PuzzleDefinition<TMeta> | null> {
      const existing = await this.getDefinition(puzzle_type);
      if (existing) return existing as PuzzleDefinition<TMeta>;
      return await this.requestNewPuzzle(puzzle_type, size, difficulty);
    },

    async cache_puzzle_ids<TMeta>(puzzle_ids: string[]): Promise<PuzzleDefinition<TMeta>[]> {
      const promises = puzzle_ids.map(pid => this.getDefinitionByID(pid));
      return await Promise.all(promises) as PuzzleDefinition<TMeta>[];
    },

  },
});
