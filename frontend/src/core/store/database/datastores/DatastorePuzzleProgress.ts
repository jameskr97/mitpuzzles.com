import { BaseRepository } from "@/core/store/database/core/BaseRepository.ts";
import type { DatabaseConnection } from "@/core/store/database/core/DatabaseConnection.ts";

interface PuzzleProgressData {
  id: string;
  used_tutorial: boolean;
  timestamp_start: number | null;
  timestamp_finish: number | null;
  state: number[][] | null;
  gutter_markings: any | null;
  lastUpdated: number;
}

export class DatastorePuzzleProgress extends BaseRepository<PuzzleProgressData> {
  protected storeName = "puzzle-progress";

  constructor(db: DatabaseConnection) {
    super(db);
  }

  async update(puzzle_type: string, updates: Partial<Omit<PuzzleProgressData, "id">>): Promise<void> {
    const existing = await this.get(puzzle_type);
    const merged: PuzzleProgressData = {
      // update essentials
      id: puzzle_type,
      lastUpdated: Date.now(),

      // set defaults here
      timestamp_start: null,
      timestamp_finish: null,
      state: null,
      used_tutorial: false,
      gutter_markings: null,

      // overried with existing then updates
      ...existing,
      ...updates,
    };

    await this.put(merged);
  }
}
