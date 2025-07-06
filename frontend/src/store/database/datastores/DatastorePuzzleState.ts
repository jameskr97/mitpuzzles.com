import { BaseRepository } from "@/store/database/core/BaseRepository.ts";
import type { DatabaseConnection } from "@/store/database/core/DatabaseConnection.ts";

interface PuzzleStateData {
  id: string;
  state: number[][];
  lastUpdated: number;
}

export class DatastorePuzzleState extends BaseRepository<PuzzleStateData> {
  protected storeName = "puzzle-state";

  constructor(db: DatabaseConnection) {
    super(db);
  }

  async setPuzzleState(puzzle_type: string, currentState: number[][]): Promise<void> {
    const puzzleState: PuzzleStateData = {
      id: puzzle_type,
      state: JSON.parse(JSON.stringify(currentState)),
      lastUpdated: Date.now(),
    };

    await this.put(puzzleState);
  }

  async getPuzzleState(puzzle_type: string): Promise<number[][] | null> {
    const result = await this.get(puzzle_type);

    if (result?.state) {
      try {
        return result.state;
      } catch (error) {
        console.warn(`Failed to parse puzzle state for ${puzzle_type}:`, error);
        return null;
      }
    }
    return null;
  }

  async deletePuzzleState(puzzle_type: string): Promise<void> {
    await this.delete(puzzle_type);
  }

  async getAllPuzzleStates(): Promise<Record<string, number[][]>> {
    const results = await this.getAll();
    const states: Record<string, number[][]> = {};

    for (const item of results) {
      if (item.state) {
        states[item.id] = item.state;
      }
    }

    return states;
  }

  async clearStates(): Promise<void> {
    await this.clear();
  }

  async getStatesCount(): Promise<number> {
    return this.count();
  }

  async getStateLastUpdated(puzzle_type: string): Promise<number | null> {
    const result = await this.get(puzzle_type);
    return result?.lastUpdated || null;
  }
}
