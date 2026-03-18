/**
 * puzzle history store - tracks user actions and events for replay/analysis
 *
 * manages:
 * - recording every user interaction with puzzles
 * - experiment-specific events and custom data
 * - chronological ordering with timestamps and sequence numbers
 * - persistence to indexeddb for research purposes
 */

import { defineStore } from "pinia";
import { databaseManager } from "@/core/store/database";
import { usePuzzleProgressStore } from "@/core/store/puzzle/usePuzzleProgressStore.ts";
import { getCurrentPuzzleID } from "@/core/store/puzzle/usePuzzleDefinitionStore.ts";
import type { GameEvent, GameActionType } from "@/core/store/database/types.ts";
import { createLogger } from "@/core/services/logger.ts";
const log = createLogger("puzzle_history");

interface HistoryState {
  events: Record<string, GameEvent[]>; // key: puzzle_type-mode or experiment_id-mode
  initialized: boolean;
  next_sequence: Record<string, number>; // track sequence per puzzle-mode or experiment-mode
}

export const usePuzzleHistoryStore = defineStore("game.history", {
  state: (): HistoryState => ({
    initialized: false,
    events: {}, // { "freeplay-sudoku": [event1, event2, ...], "experiment-metacognition": [event3, ...] }
    next_sequence: {}, // { "freeplay-sudoku": 5, "experiment-metacognition": 3 }
  }),

  getters: {
    /** gets events for a specific discriminator and mode */
    get_events: (state) => (discriminator: string, mode: "freeplay" | "experiment") => {
      const key = `${discriminator}-${mode}`;
      return state.events[key] || [];
    },

    /** calculates total active time (ms) from visibility events */
    get_active_time_ms: (state) => (discriminator: string, mode: "freeplay" | "experiment"): number => {
      const key = `${discriminator}-${mode}`;
      const events = state.events[key] || [];

      let total_active_ms = 0;
      let last_visible_timestamp: number | null = null;

      for (const event of events) {
        if (event.action_type === "puzzle_visible") {
          last_visible_timestamp = event.timestamp;
        } else if (event.action_type === "puzzle_not_visible" && last_visible_timestamp !== null) {
          total_active_ms += event.timestamp - last_visible_timestamp;
          last_visible_timestamp = null;
        }
      }

      // if puzzle is still visible, add time from last visible to now
      if (last_visible_timestamp !== null) {
        total_active_ms += Date.now() - last_visible_timestamp;
      }

      return total_active_ms;
    },
  },

  actions: {
    /** loads all event history from indexeddb into reactive state */
    async init(): Promise<void> {
      if (this.initialized) return;
      await databaseManager.init();

      const all_events = await databaseManager.history.getAll();
      
      // group events by discriminator-mode (puzzle_type for freeplay, experiment_id for experiments)
      for (const event of all_events) {
        const discriminator = event.mode === "experiment" ? event.experiment_id : event.puzzle_type;
        const key = `${discriminator}-${event.mode}`;
        if (!this.events[key]) this.events[key] = [];
        this.events[key].push(event);
        
        // track highest sequence number
        this.next_sequence[key] = Math.max(this.next_sequence[key] || 0, event.sequence + 1);
      }
      
      // sort all event arrays by sequence
      for (const key in this.events) {
        this.events[key].sort((a, b) => a.sequence - b.sequence);
      }
      
      this.initialized = true;
    },

    /** adds a new event to history */
    async add_event(
      puzzle_type: string,
      mode: "freeplay" | "experiment",
      action_type: GameActionType,
      data: Partial<Pick<GameEvent, "cell" | "key" | "old_value" | "new_value" | "board_snapshot" | "custom_data">>
    ): Promise<void> {
      // get experiment_id for experiment events
      const experiment_id = data.custom_data?.experiment_id;
      const discriminator = mode === "experiment" ? experiment_id : puzzle_type;
      const key = `${discriminator}-${mode}`;
      const sequence = this.next_sequence[key] || 1;
      const timestamp = Date.now();
      
      // generate ID based on mode
      const id = mode === "experiment"
        ? `experiment-${experiment_id}-${timestamp}`
        : `freeplay-${puzzle_type}-${timestamp}`;
      
      const event: GameEvent = {
        id,
        puzzle_type,
        mode,
        experiment_id: mode === "experiment" ? experiment_id : undefined,
        timestamp,
        sequence,
        action_type,
        ...data
      };
      
      // save to database
      await databaseManager.history.put(event);
      
      // update reactive state
      if (!this.events[key]) this.events[key] = [];
      this.events[key].push(event);
      this.next_sequence[key] = sequence + 1;
    },

    /**
     * clears all events for a puzzle and mode
     *
     * @param discriminator - type of puzzle (sudoku, tents, etc) or experiment_id
     **/
    async clear_events(discriminator: string, mode: "freeplay" | "experiment"): Promise<void> {
      const key = `${discriminator}-${mode}`;
      await databaseManager.history.clear_events(discriminator, mode);
      delete this.events[key];
      delete this.next_sequence[key];
    },

    /** builds the upload payload for a puzzle attempt */
    get_upload_payload(puzzle_type: string, mode: "freeplay" | "experiment" = "freeplay"): Record<string, any> | null {
      const events = this.get_events(puzzle_type, mode);

      if (events.length === 0) {
        return null;
      }

      const progressStore = usePuzzleProgressStore();

      // Get puzzle info for the API call
      const puzzle_id = getCurrentPuzzleID(puzzle_type);
      const start_timestamp = progressStore.timestamp_start[puzzle_type];
      const finish_timestamp = progressStore.timestamp_finish[puzzle_type];
      const final_board_state = progressStore.current_puzzle_states[puzzle_type];

      // Calculate visibility metrics
      const total_visible_ms = this.get_active_time_ms(puzzle_type, mode);
      const visible_periods = events.filter(e => e.action_type === "puzzle_visible").length;

      // Transform events to match backend expected format
      const action_history_events = events.map(event => ({
        action: event.action_type,
        timestamp: event.timestamp,
        sequence: event.sequence,
        cell: event.cell,
        key: event.key,
        old_value: event.old_value,
        new_value: event.new_value,
        board_snapshot: event.board_snapshot,
        custom_data: event.custom_data,
      }));

      // Add visibility summary as final event
      action_history_events.push({
        action: "visibility_summary",
        timestamp: Date.now(),
        sequence: events.length + 1,
        cell: undefined,
        key: undefined,
        old_value: undefined,
        new_value: undefined,
        board_snapshot: undefined,
        custom_data: {
          total_visible_ms,
          visible_periods,
        },
      });

      return {
        puzzle_id: puzzle_id,
        timestamp_start: start_timestamp,
        timestamp_finish: finish_timestamp,
        action_history: action_history_events,
        board_state: final_board_state,
        is_solved: progressStore.is_puzzle_solved(puzzle_type),
        used_tutorial: progressStore.used_tutorial[puzzle_type] || false
      };
    },

    /** uploads event history to server when puzzle is completed */
    async upload_attempt_history(puzzle_type: string, mode: "freeplay" | "experiment" = "freeplay"): Promise<void> {
      const events = this.get_events(puzzle_type, mode);

      if (events.length === 0) {
        console.warn(`No events to upload for ${puzzle_type} in mode ${mode}`);
        return;
      }

      // check if all events are visibility events - if so, don't submit
      const has_non_visibility_events = events.some(
        event => event.action_type !== "puzzle_visible" && event.action_type !== "puzzle_not_visible"
      );

      if (!has_non_visibility_events) {
        log("Skipping upload for %s - only visibility events", puzzle_type);
        return;
      }

      const payload = this.get_upload_payload(puzzle_type, mode);
      if (!payload) {
        console.warn(`No payload to upload for ${puzzle_type} in mode ${mode}`);
        return;
      }

      try {
        const response = await fetch('/api/puzzle/freeplay/submit', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        if (!response.ok) {
          throw new Error(`Upload failed: ${response.statusText}`);
        }
      } catch (error) {
        console.error('Failed to upload attempt history:', error);
        throw error;
      }
    },

  },
});
