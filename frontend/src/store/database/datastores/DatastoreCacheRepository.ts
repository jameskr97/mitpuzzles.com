import { BaseRepository } from "@/store/database/core/BaseRepository.ts";
import type { DatabaseConnection } from "@/store/database/core/DatabaseConnection.ts";

interface CacheInfo {
  id: string;
  currentVersion: number;
}

export class DatastoreCacheRepository extends BaseRepository<CacheInfo> {
  protected storeName = "cache-info";
  private readonly CACHE_INFO_ID = "cache-info";

  constructor(db: DatabaseConnection) {
    super(db);
  }

  async getCacheVersion(): Promise<number> {
    const result = await this.get(this.CACHE_INFO_ID);
    return result?.currentVersion || 0;
  }

  async setCacheVersion(version: number): Promise<void> {
    const cacheInfo: CacheInfo = {
      id: this.CACHE_INFO_ID,
      currentVersion: version,
    };

    await this.put(cacheInfo);
  }

  async clearCache(): Promise<void> {
    await this.clear();
  }

  async getCacheInfo(): Promise<CacheInfo | null> {
    return this.get(this.CACHE_INFO_ID);
  }

  async isCacheValid(expectedVersion: number): Promise<boolean> {
    const currentVersion = await this.getCacheVersion();
    return currentVersion === expectedVersion;
  }

  async invalidateCache(): Promise<void> {
    await this.setCacheVersion(0);
  }

  async initializeCache(version: number): Promise<void> {
    const existingInfo = await this.getCacheInfo();
    if (!existingInfo) {
      await this.setCacheVersion(version);
    }
  }
}
