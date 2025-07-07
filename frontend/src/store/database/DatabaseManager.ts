import { DatabaseConnection } from "./core/DatabaseConnection";
import { DatastorePuzzleDefinitions } from "./datastores/DatastorePuzzleDefinition";
import { DatastorePuzzleMetadata } from "./datastores/DatastorePuzzleMetadata";
import { DatastorePuzzleScales } from "./datastores/DatastorePuzzleScales";
import { DatastorePuzzleAttempts } from "./datastores/DatastorePuzzleAttempt";
import { DatastorePuzzleState } from "./datastores/DatastorePuzzleState";
import { DatastorePuzzleHistory } from "./datastores/DatastorePuzzleHistory";
import { DatastoreCacheRepository } from "./datastores/DatastoreCacheRepository";
import { DatastorePuzzleLeaderboard } from "./datastores/DatastorePuzzleLeaderboard";

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
  public leaderboard: DatastorePuzzleLeaderboard;

  constructor() {
    this.connection = new DatabaseConnection();
    this.definitions = new DatastorePuzzleDefinitions(this.connection);
    this.metadata = new DatastorePuzzleMetadata(this.connection);
    this.scales = new DatastorePuzzleScales(this.connection);
    this.attempts = new DatastorePuzzleAttempts(this.connection);
    this.state = new DatastorePuzzleState(this.connection);
    this.history = new DatastorePuzzleHistory(this.connection);
    this.cache = new DatastoreCacheRepository(this.connection);
    this.leaderboard = new DatastorePuzzleLeaderboard(this.connection);
  }

  async init(): Promise<void> {
    await this.connection.init();
  }

  async clearAll(): Promise<void> {
    await Promise.all([
      this.definitions.clear(),
      this.metadata.clear(),
      this.scales.clear(),
      this.attempts.clear(),
      this.state.clear(),
      this.history.clear(),
      this.cache.clear(),
      this.leaderboard.clear(),
    ]);
  }

  async getDBSize(): Promise<{
    definitions: number;
    metadata: number;
    scales: number;
    attempts: number;
    leaderboards: number;
  }> {
    const [definitions, metadata, scales, attempts, leaderboards] = await Promise.all([
      this.definitions.getDefinitionsCount(),
      this.metadata.getMetadataCount(),
      this.scales.count(),
      this.attempts.getAttemptsCount(),
      this.leaderboard.getLeaderboardCount(),
    ]);

    return { definitions, metadata, scales, attempts, leaderboards };
  }
}

// Singleton instance
export const databaseManager = new DatabaseManager();
