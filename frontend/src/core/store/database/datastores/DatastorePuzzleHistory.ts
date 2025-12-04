import { BaseRepository } from "@/core/store/database/core/BaseRepository.ts";
import type { DatabaseConnection } from "@/core/store/database/core/DatabaseConnection.ts";
import type { GameEvent } from "@/core/store/database/types.ts";

export class DatastorePuzzleHistory extends BaseRepository<GameEvent> {
  protected storeName = "puzzle-history";

  constructor(db: DatabaseConnection) {
    super(db);
  }

  async get_events(discriminator: string, mode: "freeplay" | "experiment"): Promise<GameEvent[]> {
    const all = await this.getAll();
    return all
      .filter(e => {
        if (mode === "freeplay") {
          return e.puzzle_type === discriminator && e.mode === mode;
        } else {
          // For experiments, match by experiment_id
          return e.experiment_id === discriminator && e.mode === mode;
        }
      })
      .sort((a, b) => a.sequence - b.sequence);
  }

  async clear_events(discriminator: string, mode?: "freeplay" | "experiment"): Promise<void> {
    const all = await this.getAll();
    const to_delete = all
      .filter(e => {
        if (mode === "freeplay" || !mode) {
          return e.puzzle_type === discriminator && (!mode || e.mode === mode);
        } else if (mode === "experiment") {
          return e.experiment_id === discriminator && e.mode === mode;
        }
        return false;
      })
      .map(e => e.id);
    
    for (const id of to_delete) {
      await this.delete(id);
    }
  }
}
