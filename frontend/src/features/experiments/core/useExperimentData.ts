import { ref, readonly } from "vue";
import type {
  ExperimentData,
  ExperimentMetadata,
  InterruptionData,
  PuzzleMoveData,
  PuzzleTrialData,
  StepData,
} from "./types";

class ExperimentDataDB {
  private db: IDBDatabase | null = null;
  private readonly DB_NAME = "experiment_data";
  private readonly DB_VERSION = 1;
  private readonly STORES = {
    EXPERIMENTS: "experiments",
    MOVES: "puzzle_moves",
    BACKUPS: "data_backups",
  };

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

        // Main experiment data store
        if (!db.objectStoreNames.contains(this.STORES.EXPERIMENTS)) {
          const experimentStore = db.createObjectStore(this.STORES.EXPERIMENTS, { keyPath: "sessionId" });
          experimentStore.createIndex("experimentId", "experimentId");
          experimentStore.createIndex("participantId", "participantId");
        }

        // High-frequency move data store
        if (!db.objectStoreNames.contains(this.STORES.MOVES)) {
          const moveStore = db.createObjectStore(this.STORES.MOVES, {
            keyPath: ["sessionId", "trialId", "moveIndex"],
          });
          moveStore.createIndex("sessionId", "sessionId");
          moveStore.createIndex("trialId", "trialId");
        }

        // Backup store for data export
        if (!db.objectStoreNames.contains(this.STORES.BACKUPS)) {
          db.createObjectStore(this.STORES.BACKUPS, { keyPath: "timestamp" });
        }
      };
    });
  }

  async saveExperiment(data: ExperimentData): Promise<void> {
    await this.init();
    if (!this.db) throw new Error("Database not initialized");

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([this.STORES.EXPERIMENTS], "readwrite");
      const store = transaction.objectStore(this.STORES.EXPERIMENTS);

      const request = store.put(data);
      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve();
    });
  }

  async getExperiment(sessionId: string): Promise<ExperimentData | null> {
    await this.init();
    if (!this.db) return null;

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([this.STORES.EXPERIMENTS], "readonly");
      const store = transaction.objectStore(this.STORES.EXPERIMENTS);

      const request = store.get(sessionId);
      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve(request.result || null);
    });
  }

  async saveMoves(sessionId: string, trialId: string, moves: PuzzleMoveData[]): Promise<void> {
    await this.init();
    if (!this.db) throw new Error("Database not initialized");

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([this.STORES.MOVES], "readwrite");
      const store = transaction.objectStore(this.STORES.MOVES);

      const savePromises = moves.map((move, index) => {
        return new Promise<void>((resolve, reject) => {
          const request = store.put({
            sessionId,
            trialId,
            moveIndex: index,
            ...move,
          });
          request.onerror = () => reject(request.error);
          request.onsuccess = () => resolve();
        });
      });

      Promise.all(savePromises)
        .then(() => resolve())
        .catch(reject);
    });
  }

  async getMoves(sessionId: string, trialId?: string): Promise<PuzzleMoveData[]> {
    await this.init();
    if (!this.db) return [];

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([this.STORES.MOVES], "readonly");
      const store = transaction.objectStore(this.STORES.MOVES);
      const index = store.index("sessionId");

      const request = index.getAll(sessionId);
      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        let moves = request.result || [];
        if (trialId) {
          moves = moves.filter((m) => m.trialId === trialId);
        }
        resolve(moves.sort((a, b) => a.moveIndex - b.moveIndex));
      };
    });
  }

  async createBackup(sessionId: string): Promise<string> {
    const experiment = await this.getExperiment(sessionId);
    const moves = await this.getMoves(sessionId);

    const backup = {
      timestamp: Date.now(),
      sessionId,
      experiment,
      moves,
      version: "1.0",
    };

    await this.init();
    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([this.STORES.BACKUPS], "readwrite");
      const store = transaction.objectStore(this.STORES.BACKUPS);

      const request = store.put(backup);
      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve(JSON.stringify(backup));
    });
  }

  async clearSession(sessionId: string): Promise<void> {
    await this.init();
    if (!this.db) return;

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([this.STORES.EXPERIMENTS, this.STORES.MOVES], "readwrite");

      // Clear experiment data
      const expStore = transaction.objectStore(this.STORES.EXPERIMENTS);
      expStore.delete(sessionId);

      // Clear move data
      const moveStore = transaction.objectStore(this.STORES.MOVES);
      const index = moveStore.index("sessionId");
      const deleteRequest = index.openCursor(sessionId);

      deleteRequest.onsuccess = (event) => {
        const cursor = (event.target as IDBRequest).result;
        if (cursor) {
          cursor.delete();
          cursor.continue();
        }
      };

      transaction.oncomplete = () => resolve();
      transaction.onerror = () => reject(transaction.error);
    });
  }
}

const experimentDB = new ExperimentDataDB();

export function useExperimentData(sessionId: string) {
  const experimentData = ref<ExperimentData | null>(null);
  const currentTrialMoves = ref<PuzzleMoveData[]>([]);
  const saveQueue = ref<any[]>([]);
  const lastSaveTime = ref(0);

  let saveInterval: NodeJS.Timeout | null = null;

  // Initialize or load existing experiment data
  async function initializeExperiment(experimentId: string, participantId: string): Promise<ExperimentData> {
    // Try to load existing session first
    const existing = await experimentDB.getExperiment(sessionId);
    if (existing) {
      experimentData.value = existing;
      return existing;
    }

    // Create new experiment data
    const newData: ExperimentData = {
      sessionId,
      experimentId,
      participantId,
      startTime: Date.now(),
      abTestAssignment: undefined,
      steps: [],
      puzzleTrials: [],
      interruptions: [],
      metadata: collectMetadata(),
    };

    experimentData.value = newData;
    await saveExperimentData();
    return newData;
  }

  // Save experiment data (steps, trials, etc.)
  async function saveExperimentData(): Promise<void> {
    // if (!experimentData.value) return;
    //
    // try {
    //   await experimentDB.saveExperiment(experimentData.value);
    //   lastSaveTime.value = Date.now();
    // } catch (error) {
    //   console.error("Failed to save experiment data:", error);
    //   // Add to queue for retry
    //   saveQueue.value.push({ type: "experiment", data: experimentData.value });
    // }
  }

  // Save individual puzzle move (high frequency)
  async function savePuzzleMove(trialId: string, move: PuzzleMoveData): Promise<void> {
    currentTrialMoves.value.push(move);

    try {
      // Save immediately for data integrity
      await experimentDB.saveMoves(sessionId, trialId, [move]);
    } catch (error) {
      console.error("Failed to save puzzle move:", error);
      // Add to queue for retry
      saveQueue.value.push({ type: "move", trialId, data: move });
    }
  }

  // Record step completion
  function recordStepCompletion(stepData: StepData): void {
    if (!experimentData.value) return;

    const existingIndex = experimentData.value.steps.findIndex((s) => s.stepId === stepData.stepId);
    if (existingIndex >= 0) {
      experimentData.value.steps[existingIndex] = stepData;
    } else {
      experimentData.value.steps.push(stepData);
    }

    saveExperimentData();
  }

  // Start a new puzzle trial
  function startPuzzleTrial(trialData: Partial<PuzzleTrialData>): string {
    if (!experimentData.value) throw new Error("Experiment not initialized");

    const trial: PuzzleTrialData = {
      trialId: `${sessionId}_trial_${experimentData.value.puzzleTrials.length}`,
      puzzleType: trialData.puzzleType!,
      puzzleDefinition: trialData.puzzleDefinition,
      startTime: Date.now(),
      completed: false,
      moves: [],
      interruptions: [],
      finalState: null,
      metadata: trialData.metadata || {},
    };

    experimentData.value.puzzleTrials.push(trial);
    currentTrialMoves.value = [];
    saveExperimentData();

    return trial.trialId;
  }

  // Complete a puzzle trial
  function completePuzzleTrial(trialId: string, finalState: any, completed: boolean = true): void {
    if (!experimentData.value) return;

    const trial = experimentData.value.puzzleTrials.find((t) => t.trialId === trialId);
    if (!trial) return;

    trial.endTime = Date.now();
    trial.completed = completed;
    trial.finalState = finalState;
    trial.moves = [...currentTrialMoves.value];

    saveExperimentData();
  }

  // Record interruption
  function recordInterruption(interruptionData: InterruptionData): void {
    if (!experimentData.value) return;

    experimentData.value.interruptions.push(interruptionData);

    // Also add to the trial's interruption list
    const trial = experimentData.value.puzzleTrials.find((t) => t.trialId === interruptionData.trialId);
    if (trial) {
      trial.interruptions.push(interruptionData.interruptionId);
    }

    saveExperimentData();
  }

  // Complete experiment
  async function completeExperiment(): Promise<string> {
    if (!experimentData.value) throw new Error("Experiment not initialized");

    experimentData.value.endTime = Date.now();
    await saveExperimentData();

    // Create final backup for export
    return await experimentDB.createBackup(sessionId);
  }

  // Export data as JSON
  async function exportData(): Promise<string> {
    return await experimentDB.createBackup(sessionId);
  }

  // Start periodic saves
  function startPeriodicSave(intervalMs: number = 30000): void {
    if (saveInterval) clearInterval(saveInterval);

    saveInterval = setInterval(async () => {
      await saveExperimentData();

      // Process save queue
      for (const item of saveQueue.value) {
        try {
          if (item.type === "experiment") {
            await experimentDB.saveExperiment(item.data);
          } else if (item.type === "move") {
            await experimentDB.saveMoves(sessionId, item.trialId, [item.data]);
          }
        } catch (error) {
          console.error("Failed to process queued save:", error);
          continue;
        }
      }
      saveQueue.value = [];
    }, intervalMs);
  }

  // Stop periodic saves
  function stopPeriodicSave(): void {
    if (saveInterval) {
      clearInterval(saveInterval);
      saveInterval = null;
    }
  }

  // Clear all data for this session
  async function clearSessionData(): Promise<void> {
    await experimentDB.clearSession(sessionId);
    experimentData.value = null;
    currentTrialMoves.value = [];
    saveQueue.value = [];
  }

  // Collect browser/environment metadata
  function collectMetadata(): ExperimentMetadata {
    return {
      userAgent: navigator.userAgent,
      screenSize: {
        width: window.screen.width,
        height: window.screen.height,
      },
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      language: navigator.language,
      experiment_version: "1.0.0", // TODO: get from config
      framework_version: "1.0.0",
    };
  }

  return {
    // State
    experimentData: readonly(experimentData),
    currentTrialMoves: readonly(currentTrialMoves),
    lastSaveTime: readonly(lastSaveTime),

    // Methods
    initializeExperiment,
    saveExperimentData,
    savePuzzleMove,
    recordStepCompletion,
    startPuzzleTrial,
    completePuzzleTrial,
    recordInterruption,
    completeExperiment,
    exportData,
    clearSessionData,
    startPeriodicSave,
    stopPeriodicSave,
  };
}
