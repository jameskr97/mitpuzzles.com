/**
 * puzzle progress store - tracks timing and state for puzzles
 *
 * manages:
 * - start/finish timestamps for each puzzle
 * - current puzzle state (board positions)
 * - reactive time display with millisecond precision
 * - persistence to indexeddb
 */
import { defineStore } from "pinia";
import { databaseManager } from "@/store/database";
import { ref } from "vue";
import { broadcast_channel_service } from "@/services/broadcast_channel";

// constants + types
type Precision = "seconds" | "centiseconds";
const UPDATE_INTERVAL_MS = 16; // 60fps for smooth millisecond updates
const CURRENT_TIME = ref(Date.now());
setInterval(() => (CURRENT_TIME.value = Date.now()), UPDATE_INTERVAL_MS);

interface PuzzleProgressState {
  initialized: boolean;
  timestamp_start: Record<string, number>; // when puzzle first presented
  timestamp_finish: Record<string, number>; // when submit is clicked
  current_puzzle_states: Record<string, number[][]>; // current board state
  used_tutorial: Record<string, boolean>; // whether tutorial was used with violations shown
  displayPrecision: Precision; // show seconds or milliseconds
  updateInterval: NodeJS.Timeout | null; // unused, kept for compatibility
  broadcast_unsubscribers: (() => void)[]; // cleanup functions for broadcast listeners
}

export const usePuzzleProgressStore = defineStore("puzzle.progress", {
  state: (): PuzzleProgressState => ({
    initialized: false,
    timestamp_start: {},
    timestamp_finish: {},
    current_puzzle_states: {},
    used_tutorial: {},
    displayPrecision: "seconds",
    updateInterval: null,
    broadcast_unsubscribers: [],
  }),

  getters: {
    /**
     * formats elapsed time for display
     * returns formats: MM:SS.CC, H:MM:SS.CC, or Dd:HH:MM:SS.CC
     * shows centiseconds (.CC) when precision is centiseconds
     */
    get_formatted_time:
      (state) =>
      (puzzle_type: string): string => {
        const time_start = state.timestamp_start[puzzle_type];
        if (!time_start) return "00:00";
        const time_finish = state.timestamp_finish[puzzle_type] ?? CURRENT_TIME.value;

        // math.max because sometimes finish < start due to UPDATE_INTERVAL_MS not being instant
        const elapsed_ms = Math.max(0, time_finish - time_start);

        const days = Math.floor(elapsed_ms / (1000 * 60 * 60 * 24));
        const hours = Math.floor((elapsed_ms % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutes = Math.floor((elapsed_ms % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((elapsed_ms % (1000 * 60)) / 1000);
        const centiseconds = Math.floor((elapsed_ms % 1000) / 10);

        // format based on largest unit
        let formatted_time;
        if (days > 0) {
          formatted_time = `${days}d:${hours.toString().padStart(2, "0")}:${minutes.toString().padStart(2, "0")}:${seconds.toString().padStart(2, "0")}`;
        } else if (hours > 0) {
          formatted_time = `${hours}:${minutes.toString().padStart(2, "0")}:${seconds.toString().padStart(2, "0")}`;
        } else {
          formatted_time = `${minutes.toString().padStart(2, "0")}:${seconds.toString().padStart(2, "0")}`;
        }
        if (state.displayPrecision === "centiseconds") formatted_time += `.${centiseconds.toString().padStart(2, "0")}`;

        return formatted_time;
      },

    /** checks if puzzle has been completed (has finish timestamp) */
    is_puzzle_solved:
      (s) =>
      (ptype: string): boolean =>
        ptype in s.timestamp_finish,
  },

  actions: {
    /** loads all puzzle progress from indexeddb into reactive state */
    async init(): Promise<void> {
      if (this.initialized) return;
      await databaseManager.init();

      // for each puzzle, add relevant data to pinia store
      const all_progress = await databaseManager.progress.getAll();
      for (const game of all_progress) {
        if (game.timestamp_start) this.timestamp_start[game.id] = game.timestamp_start;
        if (game.timestamp_finish) this.timestamp_finish[game.id] = game.timestamp_finish;
        if (game.state) this.current_puzzle_states[game.id] = game.state;
        if (game.used_tutorial) this.used_tutorial[game.id] = game.used_tutorial;
      }

      this.setup_broadcast_listeners();
      this.initialized = true;
    },

    /** saves current puzzle board state to memory and database */
    async update_puzzle_state(puzzle_type: string, new_state: number[][], is_source_action = true) {
      this.current_puzzle_states[puzzle_type] = new_state;
      
      // only save to database if this tab initiated the action
      if (is_source_action) {
        databaseManager.progress.update(puzzle_type, { state: JSON.parse(JSON.stringify(new_state)) });
        broadcast_channel_service.broadcast_state_update(puzzle_type, new_state);
      }
    },

    /** resets puzzle - clears progress, sets new start time, saves initial state */
    async reset_puzzle(puzzle_type: string, initial_state: number[][]) {
      await databaseManager.progress.delete(puzzle_type);

      this.timestamp_start[puzzle_type] = Date.now();
      this.current_puzzle_states[puzzle_type] = initial_state;
      delete this.timestamp_finish[puzzle_type]; // if not present, puzzle is in progress
      delete this.used_tutorial[puzzle_type]; // reset tutorial usage

      await databaseManager.progress.update(puzzle_type, {
        timestamp_start: this.timestamp_start[puzzle_type],
        timestamp_finish: null,
        state: JSON.parse(JSON.stringify(initial_state)),
        used_tutorial: false,
      });
      broadcast_channel_service.broadcast_game_reset(puzzle_type, initial_state);
    },

    /** marks puzzle as completed with current timestamp */
    async mark_puzzle_solved(puzzle_type: string) {
      this.timestamp_finish[puzzle_type] = Date.now();
      databaseManager.progress.update(puzzle_type, {
        timestamp_finish: this.timestamp_finish[puzzle_type],
      });
      broadcast_channel_service.broadcast_game_solved(puzzle_type, this.timestamp_finish[puzzle_type]);
      return this;
    },

    /** marks tutorial as used - can only be set to true, never back to false */
    async mark_tutorial_used(puzzle_type: string) {
      if (this.used_tutorial[puzzle_type]) return; // already marked, no need to update

      this.used_tutorial[puzzle_type] = true;
      await databaseManager.progress.update(puzzle_type, {
        used_tutorial: true,
      });
      broadcast_channel_service.broadcast_tutorial_used(puzzle_type);
    },

    /** toggles between seconds and millisecond precision for time display */
    async set_display_precision(show_centisecond: boolean) {
      this.displayPrecision = show_centisecond ? "centiseconds" : "seconds";
    },

    /** setup broadcast channel listeners for cross-tab sync */
    setup_broadcast_listeners() {
      console.log("Setting up puzzle progress broadcast listeners");
      // listen for game state updates from other tabs
      this.broadcast_unsubscribers.push(
        broadcast_channel_service.subscribe('game_state_update', (message) => {
          console.log("Received game state update via broadcast channel", message);
          // only update state, don't save to database (that was done by source tab)
          this.update_puzzle_state(message.puzzle_type, message.data.board_state, false);
        })
      );

      // listen for game resets from other tabs
      this.broadcast_unsubscribers.push(
        broadcast_channel_service.subscribe('game_reset', (message) => {
          this.timestamp_start[message.puzzle_type] = message.timestamp;
          this.current_puzzle_states[message.puzzle_type] = message.data.initial_state;
          delete this.timestamp_finish[message.puzzle_type];
          delete this.used_tutorial[message.puzzle_type];
        })
      );

      // listen for puzzle solved from other tabs
      this.broadcast_unsubscribers.push(
        broadcast_channel_service.subscribe('game_solved', (message) => {
          this.timestamp_finish[message.puzzle_type] = message.data.timestamp_finish;
        })
      );

      // listen for tutorial usage from other tabs
      this.broadcast_unsubscribers.push(
        broadcast_channel_service.subscribe('tutorial_used', (message) => {
          this.used_tutorial[message.puzzle_type] = true;
        })
      );
    },

    /** cleanup broadcast listeners */
    cleanup_broadcast_listeners() {
      this.broadcast_unsubscribers.forEach(unsubscribe => unsubscribe());
      this.broadcast_unsubscribers = [];
    },
  },
});
