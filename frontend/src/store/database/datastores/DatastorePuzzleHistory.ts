import { BaseRepository } from "@/store/database/core/BaseRepository.ts";
import type { DatabaseConnection } from "@/store/database/core/DatabaseConnection.ts";

export type HistoryMode = "freeplay" | "study";

// Base interface for all events - what developers work with
interface BaseEvent {
  id: string;
  puzzle_type: string;
  mode: HistoryMode;
  event_order: number;
  event_payload: any;
  created_at: number;
}

// Extended interface for experiment events - what researchers configure
interface ExperimentEvent extends BaseEvent {
  experiment_id: string;
  trial_id: string;
  session_id?: string; // Optional for grouping multiple trials
}

// Union type for both event types
type EventRecord = BaseEvent | ExperimentEvent;

// Type guards for type safety
function isExperimentEvent(event: EventRecord): event is ExperimentEvent {
  return "experiment_id" in event && "trial_id" in event;
}

function isBaseEvent(event: EventRecord): event is BaseEvent {
  return !isExperimentEvent(event);
}

export class DatastorePuzzleHistory extends BaseRepository<EventRecord> {
  protected storeName = "puzzle-history";

  constructor(db: DatabaseConnection) {
    super(db);
  }

  // DEVELOPER API - Simple puzzle history (unchanged interface)
  async addHistoryEvent(puzzle_type: string, mode: HistoryMode, event_payload: any): Promise<number> {
    const existing = await this.getAll();

    const maxOrder = existing
      .filter((e) => isBaseEvent(e) && e.puzzle_type === puzzle_type && e.mode === mode)
      .reduce((max, e) => Math.max(max, e.event_order), 0);

    const nextOrder = maxOrder + 1;
    const historyEvent: BaseEvent = {
      id: `${puzzle_type}-${mode}-${nextOrder}`,
      puzzle_type,
      mode,
      event_order: nextOrder,
      event_payload,
      created_at: Date.now(),
    };

    await this.put(historyEvent);
    return nextOrder;
  }

  // RESEARCHER API - Experiment event tracking
  async addExperimentEvent(
    experiment_id: string,
    trial_id: string,
    puzzle_type: string,
    event_payload: any,
    session_id?: string,
  ): Promise<number> {
    const existing = await this.getAll();

    // Get next sequence number within this specific trial
    const maxOrder = existing
      .filter((e) => isExperimentEvent(e) && e.experiment_id === experiment_id && e.trial_id === trial_id)
      .reduce((max, e) => Math.max(max, e.event_order), 0);

    const nextOrder = maxOrder + 1;
    const experimentEvent: ExperimentEvent = {
      id: `exp_${experiment_id}_trial_${trial_id}_${nextOrder}`,
      experiment_id,
      trial_id,
      puzzle_type,
      mode: "study", // Experiments are always in study mode
      event_order: nextOrder,
      event_payload,
      created_at: Date.now(),
      ...(session_id && { session_id }),
    };

    await this.put(experimentEvent);
    return nextOrder;
  }

  // DEVELOPER API - Get puzzle history (filtered to base events only)
  async getHistoryEvents(puzzle_type: string, mode?: HistoryMode): Promise<BaseEvent[]> {
    const allEvents = await this.getAll();

    return allEvents
      .filter(
        (event): event is BaseEvent =>
          isBaseEvent(event) && event.puzzle_type === puzzle_type && (!mode || event.mode === mode),
      )
      .sort((a, b) => a.event_order - b.event_order);
  }

  // async exportUserInputData(experiment_id, session_id = null) {
  //   const events = await this.getExperimentEvents(experiment_id);
  //   console.log(events)
  //   // Filter by session if provided
  //   const filteredEvents = session_id ? events.filter((e) => e.session_id === session_id) : events;
  //
  //   // Group by trial_id
  //   const groupedData = {};
  //   filteredEvents.forEach((event) => {
  //     if (!groupedData[event.trial_id]) {
  //       groupedData[event.trial_id] = [];
  //     }
  //     groupedData[event.trial_id].push(event.event_payload);
  //   });
  //
  //   return groupedData;
  // }

  // RESEARCHER API - Get experiment events in correct chronological order
  async getExperimentEvents(experiment_id: string, trial_id?: string): Promise<ExperimentEvent[]> {
    const allEvents = await this.getAll();

    return allEvents
      .filter(
        (event): event is ExperimentEvent =>
          isExperimentEvent(event) &&
          event.experiment_id === experiment_id &&
          (!trial_id || event.trial_id === trial_id),
      )
      .sort((a, b) => {
        // First sort by trial_id, then by event_order within trial
        if (a.trial_id !== b.trial_id) {
          return a.trial_id.localeCompare(b.trial_id);
        }
        return a.event_order - b.event_order;
      });
  }

  // RESEARCHER API - Get all trials for an experiment
  async getExperimentTrials(experiment_id: string): Promise<string[]> {
    const allEvents = await this.getAll();

    const trialIds = new Set<string>();
    allEvents
      .filter(isExperimentEvent)
      .filter((event) => event.experiment_id === experiment_id)
      .forEach((event) => trialIds.add(event.trial_id));

    return Array.from(trialIds).sort();
  }

  // RESEARCHER API - Get experiment summary data
  async getExperimentSummary(experiment_id: string): Promise<{
    experiment_id: string;
    trial_count: number;
    total_events: number;
    date_range: { start: number; end: number };
    puzzle_types: string[];
  }> {
    const events = await this.getExperimentEvents(experiment_id);

    if (events.length === 0) {
      throw new Error(`No events found for experiment: ${experiment_id}`);
    }

    const trialIds = new Set(events.map((e) => e.trial_id));
    const puzzleTypes = new Set(events.map((e) => e.puzzle_type));
    const timestamps = events.map((e) => e.created_at);

    return {
      experiment_id,
      trial_count: trialIds.size,
      total_events: events.length,
      date_range: {
        start: Math.min(...timestamps),
        end: Math.max(...timestamps),
      },
      puzzle_types: Array.from(puzzleTypes),
    };
  }

  // DEVELOPER API - Clear puzzle history (unchanged interface)
  async clearHistory(puzzle_type: string, mode?: HistoryMode): Promise<void> {
    const db = this.db.getDatabase();
    if (!db) throw new Error("Database not initialized");

    return new Promise<void>((resolve, reject) => {
      const tx = db.transaction(this.storeName, "readwrite");
      const store = tx.objectStore(this.storeName);

      const cursorReq = store.openCursor();
      cursorReq.onsuccess = (ev) => {
        const cursor = (ev.target as IDBRequest<IDBCursorWithValue>).result;
        if (!cursor) return;

        const record = cursor.value as EventRecord;
        if (isBaseEvent(record) && record.puzzle_type === puzzle_type && (!mode || record.mode === mode)) {
          cursor.delete();
        }
        cursor.continue();
      };

      cursorReq.onerror = () => reject(cursorReq.error);
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
      tx.onabort = () => reject(tx.error);
    });
  }

  // RESEARCHER API - Clear experiment data
  async clearExperiment(experiment_id: string, trial_id?: string): Promise<void> {
    const db = this.db.getDatabase();
    if (!db) throw new Error("Database not initialized");

    return new Promise<void>((resolve, reject) => {
      const tx = db.transaction(this.storeName, "readwrite");
      const store = tx.objectStore(this.storeName);

      const cursorReq = store.openCursor();
      cursorReq.onsuccess = (ev) => {
        const cursor = (ev.target as IDBRequest<IDBCursorWithValue>).result;
        if (!cursor) return;

        const record = cursor.value as EventRecord;
        if (
          isExperimentEvent(record) &&
          record.experiment_id === experiment_id &&
          (!trial_id || record.trial_id === trial_id)
        ) {
          cursor.delete();
        }
        cursor.continue();
      };

      cursorReq.onerror = () => reject(cursorReq.error);
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
      tx.onabort = () => reject(tx.error);
    });
  }

  // SHARED API - Clear all data
  async clearAllHistory(): Promise<void> {
    return this.clear();
  }

  // SHARED API - Get all events (developers get base events, researchers get all)
  async getAllHistory(): Promise<EventRecord[]> {
    return this.getAll();
  }

  // DEVELOPER API - Get puzzle history count
  async getHistoryCount(): Promise<number> {
    const events = await this.getAll();
    return events.filter(isBaseEvent).length;
  }

  // RESEARCHER API - Get experiment event count
  async getExperimentCount(experiment_id?: string): Promise<number> {
    const events = await this.getAll();
    return events.filter((e) => isExperimentEvent(e) && (!experiment_id || e.experiment_id === experiment_id)).length;
  }

  // DEVELOPER API - Get grouped puzzle history (unchanged interface)
  async getHistoryForPuzzleType(puzzle_type: string): Promise<Record<HistoryMode, BaseEvent[]>> {
    const allEvents = await this.getHistoryEvents(puzzle_type);

    const grouped: Record<HistoryMode, BaseEvent[]> = {
      freeplay: [],
      study: [],
    };

    for (const event of allEvents) {
      grouped[event.mode].push(event);
    }

    return grouped;
  }

  // RESEARCHER API - Export experiment data for analysis
  async exportExperimentData(experiment_id: string): Promise<{
    metadata: any;
    trials: Array<{
      trial_id: string;
      events: ExperimentEvent[];
      duration_ms: number;
      event_count: number;
    }>;
  }> {
    const summary = await this.getExperimentSummary(experiment_id);
    const trials = await this.getExperimentTrials(experiment_id);

    const trialData = await Promise.all(
      trials.map(async (trial_id) => {
        const events = await this.getExperimentEvents(experiment_id, trial_id);
        const timestamps = events.map((e) => e.created_at);

        return {
          trial_id,
          events,
          duration_ms: timestamps.length > 1 ? Math.max(...timestamps) - Math.min(...timestamps) : 0,
          event_count: events.length,
        };
      }),
    );

    return {
      metadata: summary,
      trials: trialData,
    };
  }

  async exportUserInputData(experiment_id, session_id = null) {
    const events = await this.getExperimentEvents(experiment_id);
    const filteredEvents = session_id ? events.filter((e) => e.experiment_id === experiment_id) : events;

    const groupedData = {};
    filteredEvents.forEach((event) => {
      if (!groupedData[event.trial_id]) {
        groupedData[event.trial_id] = [];
      }
      groupedData[event.trial_id].push(event.event_payload);
    });

    return groupedData;
  }
}
