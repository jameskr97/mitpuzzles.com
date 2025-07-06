import { defineStore } from "pinia";
import type { PuzzleDefinition } from "@/services/game/engines/types.ts";
import { ACTIVE_GAMES } from "@/constants.ts";
import { getPuzzle } from "@/services/app.ts";
import { databaseManager } from "@/store/database";

export const useGameStateStore = defineStore("game", {
  state: () => ({
    definitions: new Map<string, PuzzleDefinition>(),
    current_puzzle_states: {} as Record<string, number[][]>,
    initialized: false,
  }),

  getters: {
    getDefinition(): (puzzle_type: string) => PuzzleDefinition | null {
      return (puzzle_type: string) => {
        return this.definitions.get(puzzle_type) || null;
      };
    },

    hasDefinition(): (puzzle_type: string) => boolean {
      return (puzzle_type: string) => {
        return this.definitions.has(puzzle_type);
      };
    },

    getAllDefinitions(): PuzzleDefinition[] {
      return Array.from(this.definitions.values());
    },

    getDefinitionsByType(): Record<string, PuzzleDefinition> {
      return Object.fromEntries(this.definitions);
    },

    getCurrentPuzzleState(): (puzzle_type: string) => any | null {
      return (puzzle_type: string) => {
        return this.current_puzzle_states[puzzle_type] || null;
      };
    },

    hasCurrentPuzzleState(): (puzzle_type: string) => boolean {
      return (puzzle_type: string) => {
        return !!this.current_puzzle_states[puzzle_type];
      };
    },
  },

  actions: {
    async init(): Promise<void> {
      if (this.initialized) return;

      try {
        // Initialize database manager
        await databaseManager.init();

        // Load definitions
        const stored = await databaseManager.definitions.getAllDefinitions();
        for (const [puzzleType, definition] of Object.entries(stored)) {
          this.definitions.set(puzzleType, definition);
        }

        // Load current puzzle states for all active games
        for (const puzzle_type of Object.keys(ACTIVE_GAMES)) {
          const savedState = await databaseManager.state.getPuzzleState(puzzle_type);
          if (savedState) {
            this.current_puzzle_states[puzzle_type] = savedState;
          }
        }

        this.initialized = true;
      } catch (error) {
        console.warn("Failed to load stored puzzle data:", error);
        this.initialized = true;
      }
    },

    async setDefinition(puzzle_type: string, definition: PuzzleDefinition): Promise<void> {
      await this.init();
      this.definitions.set(puzzle_type, definition);
      try {
        await databaseManager.definitions.setDefinition(puzzle_type, definition);
      } catch (error) {
        console.warn(`Failed to persist definition for ${puzzle_type}:`, error);
      }
    },

    async requestNewPuzzle<TMeta>(
      puzzle_type: string,
      size: string,
      difficulty: string,
    ): Promise<PuzzleDefinition<TMeta>> {
      const definition = await getPuzzle(puzzle_type, size, difficulty);
      if (definition.status !== 200) {
        throw new Error("Failed to fetch new puzzle definition");
      }
      await this.setDefinition(puzzle_type, definition.data);
      return definition.data;
    },

    async getOrFetchPuzzle<TMeta>(
      puzzle_type: string,
      size: string,
      difficulty: string,
    ): Promise<PuzzleDefinition<TMeta>> {
      await this.init();
      // @ts-expect-error ignore type error
      if (this.hasDefinition(puzzle_type)) return this.getDefinition(puzzle_type)!;
      return await this.requestNewPuzzle(puzzle_type, size, difficulty);
    },

    async updatePuzzleState(puzzle_type: string, newState: any): Promise<void> {
      // Update reactive state immediately
      this.current_puzzle_states[puzzle_type] = newState;

      try {
        // Persist to database
        await databaseManager.state.setPuzzleState(puzzle_type, newState);
      } catch (error) {
        console.warn(`Failed to persist puzzle state for ${puzzle_type}:`, error);
      }
    },

    async clearPuzzleState(puzzle_type: string): Promise<void> {
      // Clear reactive state
      delete this.current_puzzle_states[puzzle_type];

      try {
        await databaseManager.state.deletePuzzleState(puzzle_type);
      } catch (error) {
        console.warn(`Failed to clear puzzle state for ${puzzle_type}:`, error);
      }
    },

    async loadPuzzleState(puzzle_type: string): Promise<any | null> {
      try {
        const savedState = await databaseManager.state.getPuzzleState(puzzle_type);
        if (savedState) {
          this.current_puzzle_states[puzzle_type] = savedState;
        }
        return savedState;
      } catch (error) {
        console.warn(`Failed to load puzzle state for ${puzzle_type}:`, error);
        return null;
      }
    },
  },
});
