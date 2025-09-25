import { BaseRepository } from "@/store/database/core/BaseRepository.ts";
import type { DatabaseConnection } from "@/store/database/core/DatabaseConnection.ts";

// clean event structure
interface GameEvent {
  id: string;                    // unique event id
  puzzle_type: string;          // sudoku, tents, etc
  mode: "freeplay" | "experiment";
  experiment_id?: string;       // for experiment events
  timestamp: number;            // when event occurred
  sequence: number;             // order index for sorting
  action_type: "click" | "keypress" | "hover" | "clear" | "tutorial_toggle" | "custom";
  
  // action-specific data
  cell?: { row: number, col: number };
  key?: string;
  old_value?: number;
  new_value?: number;
  board_snapshot?: number[][];
  
  // custom event data (for experiment events)
  custom_data?: Record<string, any>;
}

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
