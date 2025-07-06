import { BaseRepository } from "@/store/database/core/BaseRepository.ts";
import type { DatabaseConnection } from "@/store/database/core/DatabaseConnection.ts";
import type { PuzzleDefinition } from "@/services/game/engines/types";

interface StoredPuzzleDefinition extends PuzzleDefinition {
  puzzle_type: string;
}

export class DatastorePuzzleDefinitions extends BaseRepository<StoredPuzzleDefinition> {
  protected storeName = "puzzle-definitions";

  constructor(db: DatabaseConnection) {
    super(db);
  }

  async getDefinition(puzzleType: string): Promise<PuzzleDefinition | null> {
    return this.get(puzzleType);
  }

  async setDefinition(puzzleType: string, definition: PuzzleDefinition): Promise<void> {
    const storedDefinition: StoredPuzzleDefinition = {
      ...definition,
      puzzle_type: puzzleType,
    };
    await this.put(storedDefinition);
  }

  async deleteDefinition(puzzleType: string): Promise<void> {
    await this.delete(puzzleType);
  }

  async getAllDefinitions(): Promise<Record<string, PuzzleDefinition>> {
    const results = await this.getAll();
    const definitions: Record<string, PuzzleDefinition> = {};

    for (const item of results) {
      definitions[item.puzzle_type] = item;
    }

    return definitions;
  }

  async clearDefinitions(): Promise<void> {
    await this.clear();
  }

  async getDefinitionsCount(): Promise<number> {
    return this.count();
  }
}
