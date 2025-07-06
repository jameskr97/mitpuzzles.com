// Core Infrastructure (Developer Zone)
export { DatabaseConnection } from './core/DatabaseConnection';
export { BaseRepository } from './core/BaseRepository';

// Repositories (Research Zone)
export { DatastorePuzzleDefinitions } from './datastores/DatastorePuzzleDefinition';
export { DatastorePuzzleMetadata } from './datastores/DatastorePuzzleMetadata';
export { DatastorePuzzleScales } from './datastores/DatastorePuzzleScales';
export { DatastorePuzzleAttempts } from './datastores/DatastorePuzzleAttempt';
export { DatastorePuzzleState } from './datastores/DatastorePuzzleState';
export { DatastorePuzzleHistory } from './datastores/DatastorePuzzleHistory';
export { DatastoreCacheRepository } from './datastores/DatastoreCacheRepository';

// Database Manager (Orchestration)
export { DatabaseManager, databaseManager } from './DatabaseManager';

// Migration Facade (Backward Compatibility)
export { UnifiedPuzzleDB, puzzleDB } from './UnifiedPuzzleDB';

// Types
export type * from './types';

// Re-export commonly used types for convenience
export type { HistoryMode, PuzzleActionPayload } from './types';
