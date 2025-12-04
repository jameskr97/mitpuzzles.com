import { DatabaseConnection } from "./core/DatabaseConnection.ts";
import { DatastorePuzzleProgress } from "./datastores/DatastorePuzzleProgress.ts";
import { DatastorePuzzleHistory } from "./datastores/DatastorePuzzleHistory.ts";

export class DatabaseManager {
  private connection: DatabaseConnection;

  // Datastores
  public progress: DatastorePuzzleProgress;
  public history: DatastorePuzzleHistory;

  constructor() {
    this.connection = new DatabaseConnection();
    this.progress = new DatastorePuzzleProgress(this.connection);
    this.history = new DatastorePuzzleHistory(this.connection);
  }

  async init(): Promise<void> {
    await this.connection.init();
  }
}

export const databaseManager = new DatabaseManager();
