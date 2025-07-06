import { BaseRepository } from "@/store/database/core/BaseRepository.ts";
import type { DatabaseConnection } from "@/store/database/core/DatabaseConnection.ts";

interface PuzzleAttemptData {
  id: string;
  solving_time: number;
  solved: boolean;
  completion_duration_ms: number | null;
  completed_at: number | null;
}

export class DatastorePuzzleAttempts extends BaseRepository<PuzzleAttemptData> {
  protected storeName = 'puzzle-attempt';

  constructor(db: DatabaseConnection) {
    super(db);
  }

  async getPuzzleAttempt(puzzle_type: string): Promise<PuzzleAttemptData | null> {
    return this.get(puzzle_type);
  }

  async updatePuzzleAttempt(puzzle_type: string, updates: Partial<Omit<PuzzleAttemptData, 'id'>>): Promise<void> {
    const existing = await this.getPuzzleAttempt(puzzle_type);

    const merged: PuzzleAttemptData = {
      id: puzzle_type,
      solving_time: existing?.solving_time || 0,
      solved: existing?.solved || false,
      completion_duration_ms: existing?.completion_duration_ms || null,
      completed_at: existing?.completed_at || null,
      ...updates, // Override with provided updates
    };

    await this.put(merged);
  }

  async getAllPuzzleAttempts(): Promise<Record<string, PuzzleAttemptData>> {
    const results = await this.getAll();
    const attempts: Record<string, PuzzleAttemptData> = {};

    for (const item of results) {
      attempts[item.id] = item;
    }

    return attempts;
  }

  async resetPuzzleAttempt(puzzle_type: string): Promise<void> {
    await this.updatePuzzleAttempt(puzzle_type, {
      solving_time: 0,
      solved: false,
      completion_duration_ms: null,
      completed_at: null,
    });
  }

  async clearAttempts(): Promise<void> {
    await this.clear();
  }

  async getAttemptsCount(): Promise<number> {
    return this.count();
  }

  async createPuzzleAttempt(puzzle_type: string): Promise<void> {
    const defaultAttempt: PuzzleAttemptData = {
      id: puzzle_type,
      solving_time: 0,
      solved: false,
      completion_duration_ms: null,
      completed_at: null,
    };

    await this.put(defaultAttempt);
  }
}
