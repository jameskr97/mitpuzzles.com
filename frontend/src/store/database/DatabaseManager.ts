import { DatabaseConnection } from "./core/DatabaseConnection";
import { DatastorePuzzleProgress } from "./datastores/DatastorePuzzleProgress";
import { DatastorePuzzleHistory } from "./datastores/DatastorePuzzleHistory";

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
