// src/database/core/DatabaseConnection.ts
export class DatabaseConnection {
  private db: IDBDatabase | null = null;
  private readonly DB_NAME = "mitpuzzles";
  private readonly DB_VERSION = 2;

  async init(): Promise<void> {
    if (this.db) return;

    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.DB_NAME, this.DB_VERSION);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        this.db = request.result;
        resolve();
      };

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;
        this.createStores(db);
      };
    });
  }

  private createStores(db: IDBDatabase): void {
    const stores = [
      { name: "puzzle-definitions", keyPath: "puzzle_type" },
      { name: "puzzle-metadata", keyPath: "id" },
      { name: "puzzle-scales", keyPath: "id" },
      { name: "puzzle-attempt", keyPath: "id" },
      { name: "puzzle-state", keyPath: "id" },
      { name: "puzzle-history", keyPath: "id" },
      { name: "cache-info", keyPath: "id" },
    ];

    for (const store of stores) {
      if (!db.objectStoreNames.contains(store.name)) {
        db.createObjectStore(store.name, { keyPath: store.keyPath });
      }
    }
  }

  async performTransaction<T>(
    storeNames: string | string[],
    mode: IDBTransactionMode,
    operation: (stores: IDBObjectStore | IDBObjectStore[]) => IDBRequest<T>,
  ): Promise<T> {
    await this.init();
    if (!this.db) throw new Error("Database not initialized");

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(storeNames, mode);
      const stores = Array.isArray(storeNames)
        ? storeNames.map((name) => transaction.objectStore(name))
        : transaction.objectStore(storeNames);

      const request = operation(stores);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve(request.result);
    });
  }

  getDatabase(): IDBDatabase | null {
    return this.db;
  }
}
