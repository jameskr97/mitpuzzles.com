import { defineStore } from "pinia";
import type { PuzzleDefinition } from "@/services/game/engines/types.ts";
import { getNextPuzzleID } from "@/services/app.ts";
import { useSessionTrackingStore } from "@/store/useSessionTrackingStore";
import { api } from "@/services/axios.ts";

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
      puzzle_id as unknown as number;
      return await this.getDefinitionByID(puzzle_id);
    },

    /** get puzzle definition by specific puzzle ID (Workbox handles caching) */
    async getDefinitionByID(puzzle_id: number): Promise<PuzzleDefinition | null> {
      try {
        const response = await api.get<PuzzleDefinition>(`/api/puzzle/definition/${puzzle_id}`);
        return response.data;
      } catch (error) {
        console.warn(`Failed to get puzzle definition for ID ${puzzle_id}:`, error);
        return null;
      }
    },

    /** request a new puzzle from the server and set it as current */
    async requestNewPuzzle<TMeta>(puzzle_type: string, size: string, difficulty: string): Promise<PuzzleDefinition<TMeta>> {
      // Get session_id from session tracking store
      const sessionStore = useSessionTrackingStore();
      const session_id = sessionStore.session_id;

      // request 1: get next puzzle id (with priority and uniqueness enforcement)
      const res_id = await getNextPuzzleID(puzzle_type, size, difficulty, session_id);
      if (res_id.status !== 200) throw new Error("Failed to fetch new puzzle ID");

      const puzzle_id = res_id.data.puzzle_id?.toString();
      if (!puzzle_id) throw new Error("Puzzle ID missing from response");
      this.setCurrentPuzzle(puzzle_type, puzzle_id);

      // request 2: get puzzle definition by id (Workbox caches it)
      const definition = await this.getDefinitionByID(puzzle_id);
      if (!definition) throw new Error("Failed to fetch puzzle definition");

      return definition as PuzzleDefinition<TMeta>;
    },

    /** get existing puzzle or fetch a new one */
    async getOrFetchPuzzle<TMeta>(puzzle_type: string, size: string, difficulty: string): Promise<PuzzleDefinition<TMeta>> {
      const existing = await this.getDefinition(puzzle_type);
      if (existing) return existing as PuzzleDefinition<TMeta>;
      return await this.requestNewPuzzle(puzzle_type, size, difficulty);
    },

    async cache_puzzle_ids<TMeta>(puzzle_ids: number[]): Promise<PuzzleDefinition<TMeta>[]> {
      const promises = puzzle_ids.map(pid =>  this.getDefinitionByID(pid))
      return await Promise.all(promises) as PuzzleDefinition<TMeta>[];
    },

  },
});
