import { BaseRepository } from "@/store/database/core/BaseRepository.ts";
import type { DatabaseConnection } from "@/store/database/core/DatabaseConnection.ts";

interface PuzzleMetadata {
  id: string;
  variants: string[][];
  selected_variant: string[];
  cacheVersion: number;
}

export class DatastorePuzzleMetadata extends BaseRepository<PuzzleMetadata> {
  protected storeName = "puzzle-metadata";

  constructor(db: DatabaseConnection) {
    super(db);
  }

  async getMetadata(puzzleType: string): Promise<PuzzleMetadata | null> {
    return this.get(puzzleType);
  }

  async setMetadata(puzzleType: string, data: Omit<PuzzleMetadata, "id">): Promise<void> {
    const serializedData = {
      variants: JSON.parse(JSON.stringify(data.variants)),
      selected_variant: JSON.parse(JSON.stringify(data.selected_variant)),
      cacheVersion: data.cacheVersion,
    };

    await this.put({
      id: puzzleType,
      ...serializedData,
    });
  }

  async getAllMetadata(): Promise<PuzzleMetadata[]> {
    return this.getAll();
  }

  async clearMetadata(): Promise<void> {
    await this.clear();
  }

  async getMetadataCount(): Promise<number> {
    return this.count();
  }
}
