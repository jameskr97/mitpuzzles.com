// src/database/DatabaseManager.ts
import { DatabaseConnection } from "./core/DatabaseConnection";
import { DatastorePuzzleDefinitions } from "./datastores/DatastorePuzzleDefinition";
import { DatastorePuzzleMetadata } from "./datastores/DatastorePuzzleMetadata";
import { DatastorePuzzleScales } from "./datastores/DatastorePuzzleScales";
import { DatastorePuzzleAttempts } from "./datastores/DatastorePuzzleAttempt";
import { DatastorePuzzleState } from "./datastores/DatastorePuzzleState";
import { DatastorePuzzleHistory } from "./datastores/DatastorePuzzleHistory";
import { DatastoreCacheRepository } from "./datastores/DatastoreCacheRepository";

export class DatabaseManager {
  private connection: DatabaseConnection;

  // Datastores
  public definitions: DatastorePuzzleDefinitions;
  public metadata: DatastorePuzzleMetadata;
  public scales: DatastorePuzzleScales;
  public attempts: DatastorePuzzleAttempts;
  public state: DatastorePuzzleState;
  public history: DatastorePuzzleHistory;
  public cache: DatastoreCacheRepository;

  constructor() {
    this.connection = new DatabaseConnection();

    // Initialize datastores
    this.definitions = new DatastorePuzzleDefinitions(this.connection);
    this.metadata = new DatastorePuzzleMetadata(this.connection);
    this.scales = new DatastorePuzzleScales(this.connection);
    this.attempts = new DatastorePuzzleAttempts(this.connection);
    this.state = new DatastorePuzzleState(this.connection);
    this.history = new DatastorePuzzleHistory(this.connection);
    this.cache = new DatastoreCacheRepository(this.connection);
  }

  async init(): Promise<void> {
    await this.connection.init();
  }

  async clearAll(): Promise<void> {
    await Promise.all([
      this.definitions.clearDefinitions(),
      this.metadata.clearMetadata(),
      this.scales.clearScales(),
      this.attempts.clearAttempts(),
      this.state.clearStates(),
      this.history.clearAllHistory(),
      this.cache.clearCache(),
    ]);
  }

  async getDBSize(): Promise<{ definitions: number; metadata: number }> {
    const [definitions, metadata] = await Promise.all([
      this.definitions.getDefinitionsCount(),
      this.metadata.getMetadataCount(),
    ]);

    return { definitions, metadata };
  }
}

// Singleton instance
export const databaseManager = new DatabaseManager();
