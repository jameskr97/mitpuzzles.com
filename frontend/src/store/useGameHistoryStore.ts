import { defineStore } from "pinia";
import { ACTIVE_GAMES } from "@/constants.ts";
import type { PuzzleDefinition } from "@/services/game/engines/types.ts";
import { type PuzzleFreeplayAttemptPayload, submitPuzzleAttempt } from "@/services/app.ts";
import type { HistoryMode, PuzzleActionPayload } from "@/store/database";
import { databaseManager } from "@/store/database";
import { useGameAttemptStore } from "@/store/useGameAttemptStore.ts";

// Type for experiment event data in the store
interface ExperimentEventData {
  event_order: number;
  event_payload: any;
  experiment_id: string;
  trial_id: string;
  puzzle_type: string;
  created_at: number;
}

// Type for experiment attempt payload (researchers define this)
export interface PuzzleExperimentAttemptPayload {
  experiment_id: string;
  trial_id: string;
  puzzle_id: number;
  completed_at: string;
  completion_time_client_ms: number;
  action_history: any[];
  session_id?: string;
}

export const useGameHistoryStore = defineStore("game.history", {
  state: () => ({
    // DEVELOPER STATE - unchanged
    events: {} as Record<string, { event_order: number; event_payload: any }[]>,

    // RESEARCHER STATE - new experiment tracking
    experimentEvents: {} as Record<string, ExperimentEventData[]>,

    initialized: false,
  }),

  getters: {
    // DEVELOPER GETTER - unchanged
    getEvents:
      (s) =>
      (puzzle_type: string, mode: HistoryMode = "freeplay") =>
        s.events[`${puzzle_type}::${mode}`] || [],

    // RESEARCHER GETTERS - new experiment access
    getExperimentEvents: (s) => (experiment_id: string, trial_id: string) => {
      const key = `${experiment_id}::${trial_id}`;
      return s.experimentEvents[key] || [];
    },

    getExperimentTrialEvents: (s) => (experiment_id: string) => {
      const trialEvents: Record<string, ExperimentEventData[]> = {};

      Object.entries(s.experimentEvents).forEach(([key, events]) => {
        const [expId, trialId] = key.split("::");
        if (expId === experiment_id) {
          trialEvents[trialId] = events;
        }
      });

      return trialEvents;
    },

    getActiveExperiments: (s) => () => {
      const experiments = new Set<string>();
      Object.keys(s.experimentEvents).forEach((key) => {
        const [expId] = key.split("::");
        experiments.add(expId);
      });
      return Array.from(experiments);
    },


    getAllExperimentOutput: (s) => (experiment_id: string) => {

    }
  },



  actions: {
    // DEVELOPER ACTION - enhanced but backward compatible
    async initializeStore() {
      if (this.initialized) return;

      // Initialize database manager
      await databaseManager.init();

      // Load regular puzzle history (developer data)
      for (const game of Object.keys(ACTIVE_GAMES)) {
        for (const m of ["freeplay", "study"] as HistoryMode[]) {
          const ev = await databaseManager.history.getHistoryEvents(game, m);
          if (ev.length) this.events[`${game}::${m}`] = ev;
        }
      }

      // Load experiment data (researcher data)
      await this.loadExperimentData();

      this.initialized = true;
    },

    // RESEARCHER ACTION - load experiment events
    async loadExperimentData() {
      try {
        // Get all experiment IDs from database
        const allEvents = await databaseManager.history.getAllHistory();
        const experimentEventMap = new Map<string, ExperimentEventData[]>();

        allEvents.forEach((event: any) => {
          if (event.experiment_id && event.trial_id) {
            const key = `${event.experiment_id}::${event.trial_id}`;
            if (!experimentEventMap.has(key)) {
              experimentEventMap.set(key, []);
            }
            experimentEventMap.get(key)!.push({
              event_order: event.event_order,
              event_payload: event.event_payload,
              experiment_id: event.experiment_id,
              trial_id: event.trial_id,
              puzzle_type: event.puzzle_type,
              created_at: event.created_at,
            });
          }
        });

        // Sort events within each trial by order
        experimentEventMap.forEach((events) => {
          events.sort((a, b) => a.event_order - b.event_order);
        });

        this.experimentEvents = Object.fromEntries(experimentEventMap);
      } catch (error) {
        console.error("Failed to load experiment data:", error);
      }
    },

    // DEVELOPER ACTION - unchanged
    async addEvent(puzzle_type: string, mode: HistoryMode, payload: PuzzleActionPayload) {
      const order = await databaseManager.history.addHistoryEvent(puzzle_type, mode, payload);
      const key = `${puzzle_type}::${mode}`;
      (this.events[key] ||= []).push({ event_order: order, event_payload: payload });
    },

    // RESEARCHER ACTION - add experiment event
    async addExperimentEvent(
      experiment_id: string,
      trial_id: string,
      puzzle_type: string,
      payload: PuzzleActionPayload,
      session_id?: string,
    ) {
      const order = await databaseManager.history.addExperimentEvent(
        experiment_id,
        trial_id,
        puzzle_type,
        payload,
        session_id,
      );

      const key = `${experiment_id}::${trial_id}`;
      (this.experimentEvents[key] ||= []).push({
        event_order: order,
        event_payload: payload,
        experiment_id,
        trial_id,
        puzzle_type,
        created_at: Date.now(),
      });

      return order;
    },

    // DEVELOPER ACTION - unchanged
    async clearEvents(puzzle_type: string, mode: HistoryMode) {
      await databaseManager.history.clearHistory(puzzle_type, mode);

      if (mode) delete this.events[`${puzzle_type}::${mode}`];
      else {
        delete this.events[`${puzzle_type}::freeplay`];
        delete this.events[`${puzzle_type}::study`];
      }
    },

    // RESEARCHER ACTION - clear experiment data
    async clearExperimentEvents(experiment_id: string, trial_id?: string) {
      await databaseManager.history.clearExperiment(experiment_id, trial_id);

      if (trial_id) {
        // Clear specific trial
        const key = `${experiment_id}::${trial_id}`;
        delete this.experimentEvents[key];
      } else {
        // Clear entire experiment
        Object.keys(this.experimentEvents).forEach((key) => {
          const [expId] = key.split("::");
          if (expId === experiment_id) {
            delete this.experimentEvents[key];
          }
        });
      }
    },

    // DEVELOPER ACTION - unchanged
    async uploadAttemptHistory(def: PuzzleDefinition, mode: HistoryMode = "freeplay") {
      const attemptStore = useGameAttemptStore();
      const completed_at = attemptStore.getCompletionDatetime(def.puzzle_type);
      const completion_duration = attemptStore.getCompletionDuration(def.puzzle_type);

      if (!completed_at || !completion_duration) {
        console.warn(`No completion data for ${def.puzzle_type} in mode ${mode}`);
        return;
      }

      const events = this.getEvents(def.puzzle_type, mode);
      const payload: PuzzleFreeplayAttemptPayload = {
        puzzle_id: def.id,
        completed_at: new Date(completed_at).toISOString(),
        completion_time_client_ms: completion_duration,
        action_history: events.map((e) => e.event_payload),
      };

      try {
        await submitPuzzleAttempt(payload);
      } catch (error) {
        console.error(`Error uploading history for ${def.puzzle_type} in mode ${mode}:`, error);
      }
    },

    // RESEARCHER ACTION - upload experiment attempt
    async uploadExperimentAttempt(experiment_id: string, trial_id: string, def: PuzzleDefinition, session_id?: string) {
      const attemptStore = useGameAttemptStore();
      const completed_at = attemptStore.getCompletionDatetime(def.puzzle_type);
      const completion_duration = attemptStore.getCompletionDuration(def.puzzle_type);

      if (!completed_at || !completion_duration) {
        console.warn(`No completion data for experiment ${experiment_id}, trial ${trial_id}`);
        return;
      }

      const events = this.getExperimentEvents(experiment_id, trial_id);
      const payload: PuzzleExperimentAttemptPayload = {
        experiment_id,
        trial_id,
        puzzle_id: def.id,
        completed_at: new Date(completed_at).toISOString(),
        completion_time_client_ms: completion_duration,
        action_history: events.map((e) => e.event_payload),
        ...(session_id && { session_id }),
      };

      try {
        // This endpoint would need to be implemented in @/services/app.ts
        // await submitExperimentAttempt(payload);
        console.log("Experiment data ready for upload:", payload);

        // For now, log the data structure researchers would get
        return payload;
      } catch (error) {
        console.error(`Error uploading experiment data for ${experiment_id}:${trial_id}:`, error);
      }
    },

    // RESEARCHER ACTION - get experiment statistics
    async getExperimentStatistics(experiment_id: string) {
      try {
        const summary = await databaseManager.history.getExperimentSummary(experiment_id);
        const trialEvents = this.getExperimentTrialEvents(experiment_id);

        return {
          ...summary,
          trials: Object.entries(trialEvents).map(([trial_id, events]) => ({
            trial_id,
            event_count: events.length,
            duration_ms:
              events.length > 0
                ? Math.max(...events.map((e) => e.created_at)) - Math.min(...events.map((e) => e.created_at))
                : 0,
            puzzle_types: [...new Set(events.map((e) => e.puzzle_type))],
          })),
        };
      } catch (error) {
        console.error(`Error getting statistics for experiment ${experiment_id}:`, error);
        return null;
      }
    },

    // RESEARCHER ACTION - export all experiment data
    async exportExperimentData(experiment_id: string) {
      try {
        return await databaseManager.history.exportExperimentData(experiment_id);
      } catch (error) {
        console.error(`Error exporting experiment data for ${experiment_id}:`, error);
        return null;
      }
    },
  },
});
