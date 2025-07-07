import type { DatabaseConnection } from "@/store/database/core/DatabaseConnection.ts";

export abstract class BaseRepository<T> {
  protected abstract storeName: string;

  constructor(protected db: DatabaseConnection) {}

  protected async get(key: string): Promise<T | null> {
    const result = await this.db.performTransaction(this.storeName, "readonly", (store) =>
      (store as IDBObjectStore).get(key),
    );
    return result || null;
  }

  protected async put(data: T): Promise<void> {
    await this.db.performTransaction(this.storeName, "readwrite", (store) => (store as IDBObjectStore).put(data));
  }

  protected async delete(key: string): Promise<void> {
    await this.db.performTransaction(this.storeName, "readwrite", (store) => (store as IDBObjectStore).delete(key));
  }

  protected async getAll(): Promise<T[]> {
    return this.db.performTransaction(this.storeName, "readonly", (store) => (store as IDBObjectStore).getAll());
  }

  async clear(): Promise<void> {
    await this.db.performTransaction(this.storeName, "readwrite", (store) => (store as IDBObjectStore).clear());
  }

  protected async count(): Promise<number> {
    return this.db.performTransaction(this.storeName, "readonly", (store) => (store as IDBObjectStore).count());
  }
}
