export class DatabaseConnection {
  private db: IDBDatabase | null = null;
  private readonly DB_NAME = "mitpuzzles";
  private readonly DB_VERSION = 4;

  async init(): Promise<void> {
    if (this.db) return;

    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.DB_NAME, this.DB_VERSION);

      request.onerror = () => {
        console.log("[IndexedDB] on error was called");
        reject(request.error);
      };
      request.onsuccess = () => {
        console.log("[IndexedDB] Database opened successfully");
        this.db = request.result;
        resolve();
      };

      request.onupgradeneeded = (event) => {
        console.log("[IndexedDB] on upgrade needed was called");
        const db = (event.target as IDBOpenDBRequest).result;
        this.createStores(db);
      };

      request.onblocked = (_event) => {
        console.log("[IndexedDB] Database upgrade blocked");
      };
    });
  }

  private createStores(db: IDBDatabase): void {
    const stores = [
      { name: "puzzle-history", keyPath: "id" },
      { name: "puzzle-progress", keyPath: "id" },
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

    // check if all stores exist before creating transaction
    const storeNamesArray = Array.isArray(storeNames) ? storeNames : [storeNames];
    const missingStores = storeNamesArray.filter(name => !this.db!.objectStoreNames.contains(name));
    
    if (missingStores.length > 0) {
      console.warn(`[IndexedDB] Missing stores: ${missingStores.join(', ')}. recreating database...`);
      await this.recreateDatabase();
    }

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(storeNames, mode);
      const stores = Array.isArray(storeNames)
        ? storeNames.map((name) => transaction.objectStore(name))
        : transaction.objectStore(storeNames);

      const request = operation(stores);

      request.onerror = () => {
        reject(request.error);
        console.log("indexeddb performTransaction error", request.error);
      };
      request.onsuccess = () => {
        resolve(request.result);
        console.log("[IndexedDB] Transaction completed successfully");
      };
    });
  }

  private async recreateDatabase(): Promise<void> {
    if (this.db) {
      this.db.close();
    }
    
    // delete the existing database
    return new Promise((resolve, reject) => {
      const deleteRequest = indexedDB.deleteDatabase(this.DB_NAME);
      deleteRequest.onsuccess = () => {
        console.log("[IndexedDB] Database deleted successfully");
        this.db = null;
        // reinitialize with new database
        this.init().then(resolve).catch(reject);
      };
      deleteRequest.onerror = () => {
        reject(deleteRequest.error);
      };
    });
  }

  getDatabase(): IDBDatabase | null {
    return this.db;
  }
}
