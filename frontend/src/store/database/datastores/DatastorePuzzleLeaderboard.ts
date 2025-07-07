import { BaseRepository } from "@/store/database/core/BaseRepository.ts";
import type { DatabaseConnection } from "@/store/database/core/DatabaseConnection.ts";

export interface LeaderboardEntry {
  rank: number;
  display_duration: string;
  username: string;
}

export interface CachedLeaderboard {
  id: string; // composite key: puzzle_type:size:difficulty
  puzzle_type: string;
  size: string;
  difficulty: string;
  leaderboard: LeaderboardEntry[];
}

export class DatastorePuzzleLeaderboard extends BaseRepository<CachedLeaderboard> {
  protected storeName = "puzzle-leaderboard";

  constructor(db: DatabaseConnection) {
    super(db);
  }

  private getKey(puzzle_type: string, size: string, difficulty: string): string {
    return `${puzzle_type}:${size}:${difficulty}`;
  }

  async setLeaderboard(
    puzzle_type: string,
    size: string,
    difficulty: string,
    leaderboard: LeaderboardEntry[],
  ): Promise<void> {
    const key = this.getKey(puzzle_type, size, difficulty);
    const entry: CachedLeaderboard = {
      id: key,
      puzzle_type,
      size,
      difficulty,
      leaderboard,
    };
    await this.put(entry);
  }

  async loadLeaderboard(puzzle_type: string, size: string, difficulty: string): Promise<LeaderboardEntry[]> {
    const key = this.getKey(puzzle_type, size, difficulty);
    const cachedLeaderboard = await this.get(key);
    return cachedLeaderboard?.leaderboard || [];
  }

  async getLeaderboardCount(): Promise<number> {
    return this.count();
  }
}
