import { databaseManager } from "./DatabaseManager";
import type { PuzzleDefinition } from "@/services/game/engines/types";

/**
 * Migration Facade - Maintains backward compatibility while using new modular structure
 * This class delegates to the new datastore-based system
 */
export class UnifiedPuzzleDB {
  private initialized = false;

  async init(): Promise<void> {
    if (this.initialized) return;
    await databaseManager.init();
    this.initialized = true;
  }

  // Puzzle Definitions methods - delegate to definitions datastore
  async getDefinition(puzzleType: string): Promise<PuzzleDefinition | null> {
    return databaseManager.definitions.getDefinition(puzzleType);
  }

  async setDefinition(puzzleType: string, definition: PuzzleDefinition): Promise<void> {
    return databaseManager.definitions.setDefinition(puzzleType, definition);
  }

  async deleteDefinition(puzzleType: string): Promise<void> {
    return databaseManager.definitions.deleteDefinition(puzzleType);
  }

  async getAllDefinitions(): Promise<Record<string, PuzzleDefinition>> {
    return databaseManager.definitions.getAllDefinitions();
  }

  async clearDefinitions(): Promise<void> {
    return databaseManager.definitions.clearDefinitions();
  }

  // Puzzle Metadata methods - delegate to metadata datastore
  async getMetadata(puzzleType: string): Promise<any> {
    return databaseManager.metadata.getMetadata(puzzleType);
  }

  async setMetadata(puzzleType: string, data: any): Promise<void> {
    return databaseManager.metadata.setMetadata(puzzleType, data);
  }

  async getAllMetadata(): Promise<any[]> {
    return databaseManager.metadata.getAllMetadata();
  }

  async clearMetadata(): Promise<void> {
    return databaseManager.metadata.clearMetadata();
  }

  // Puzzle Scales methods - delegate to scales datastore
  async setScale(puzzle_type: string, scale: number): Promise<void> {
    return databaseManager.scales.setScale(puzzle_type, scale);
  }

  async getAllScales(): Promise<Record<string, number>> {
    return databaseManager.scales.getAllScales();
  }

  // Puzzle Attempts methods - delegate to attempts datastore
  async getPuzzleAttempt(puzzle_type: string): Promise<any> {
    return databaseManager.attempts.getPuzzleAttempt(puzzle_type);
  }

  async updatePuzzleAttempt(puzzle_type: string, updates: any): Promise<void> {
    return databaseManager.attempts.updatePuzzleAttempt(puzzle_type, updates);
  }

  async getAllPuzzleAttempts(): Promise<Record<string, any>> {
    return databaseManager.attempts.getAllPuzzleAttempts();
  }

  async resetPuzzleAttempt(puzzle_type: string): Promise<void> {
    return databaseManager.attempts.resetPuzzleAttempt(puzzle_type);
  }

  // Puzzle State methods - delegate to state datastore
  async setPuzzleState(puzzle_type: string, currentState: number[][]): Promise<void> {
    return databaseManager.state.setPuzzleState(puzzle_type, currentState);
  }

  async getPuzzleState(puzzle_type: string): Promise<number[][] | null> {
    return databaseManager.state.getPuzzleState(puzzle_type);
  }

  async deletePuzzleState(puzzle_type: string): Promise<void> {
    return databaseManager.state.deletePuzzleState(puzzle_type);
  }

  // Puzzle History methods - delegate to history datastore
  async addHistoryEvent(puzzle_type: string, mode: any, event_payload: any): Promise<number> {
    return databaseManager.history.addHistoryEvent(puzzle_type, mode, event_payload);
  }

  async getHistoryEvents(puzzle_type: string, mode?: any): Promise<any[]> {
    return databaseManager.history.getHistoryEvents(puzzle_type, mode);
  }

  async clearHistory(puzzle_type: string, mode: any): Promise<void> {
    return databaseManager.history.clearHistory(puzzle_type, mode);
  }

  // Cache methods - delegate to cache datastore
  async getCacheVersion(): Promise<number> {
    return databaseManager.cache.getCacheVersion();
  }

  async setCacheVersion(version: number): Promise<void> {
    return databaseManager.cache.setCacheVersion(version);
  }

  // Utility methods
  async clearAll(): Promise<void> {
    return databaseManager.clearAll();
  }

  async getDBSize(): Promise<{ definitions: number; metadata: number }> {
    return databaseManager.getDBSize();
  }
}

// Maintain backward compatibility
export const puzzleDB = new UnifiedPuzzleDB();
