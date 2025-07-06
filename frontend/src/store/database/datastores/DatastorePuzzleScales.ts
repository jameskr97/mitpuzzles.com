import { BaseRepository } from "@/store/database/core/BaseRepository.ts";
import type { DatabaseConnection } from "@/store/database/core/DatabaseConnection.ts";

interface PuzzleScale {
  id: string;
  scale: number;
}

export class DatastorePuzzleScales extends BaseRepository<PuzzleScale> {
  protected storeName = "puzzle-scales";

  constructor(db: DatabaseConnection) {
    super(db);
  }

  async setScale(puzzle_type: string, scale: number): Promise<void> {
    await this.put({
      id: puzzle_type,
      scale,
    });
  }

  async getScale(puzzle_type: string): Promise<number | null> {
    const result = await this.get(puzzle_type);
    return result?.scale || null;
  }

  async getAllScales(): Promise<Record<string, number>> {
    const results = await this.getAll();
    const scales: Record<string, number> = {};

    for (const item of results) {
      scales[item.id] = item.scale;
    }

    return scales;
  }

  async clearScales(): Promise<void> {
    await this.clear();
  }

  async getScalesCount(): Promise<number> {
    return this.count();
  }
}
