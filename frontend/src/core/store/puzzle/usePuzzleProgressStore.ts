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
import { databaseManager } from "@/core/store/database";
import { ref } from "vue";
import { broadcast_channel_service } from "@/core/services/broadcast_channel.ts";
import type { PuzzleDefinition } from "@/core/games/types/puzzle-types.ts";
// GutterMarkings type for nonograms row/col completion tracking
type GutterMarkings = Record<string, boolean>;
import { createLogger } from "@/core/services/logger.ts";
import { emitter } from "@/core/services/event-bus.ts";
const log = createLogger("puzzle_progress");

// events
emitter.on("daily:clear-progress", async ({ key }) => {
  const store = usePuzzleProgressStore();
  delete store.timestamp_start[key];
  delete store.timestamp_finish[key];
  delete store.current_puzzle_states[key];
  delete store.used_tutorial[key];
  delete store.gutter_markings[key];
  await databaseManager.progress.delete(key);
});

// constants + types
type Precision = "seconds" | "centiseconds";
const UPDATE_INTERVAL_MS = 16; // 60fps for smooth millisecond updates
const CURRENT_TIME = ref(Date.now());
setInterval(() => (CURRENT_TIME.value = Date.now()), UPDATE_INTERVAL_MS);

interface PuzzleProgressState {
  initialized: boolean;
  definitions: Record<string, PuzzleDefinition>; // active puzzle definitions
  timestamp_start: Record<string, number>; // when puzzle first presented
  timestamp_finish: Record<string, number>; // when submit is clicked
  current_puzzle_states: Record<string, number[][]>; // current board state
  used_tutorial: Record<string, boolean>; // whether tutorial was used with violations shown
  gutter_markings: Record<string, GutterMarkings>; // gutter completion markings
  displayPrecision: Precision; // show seconds or milliseconds
  updateInterval: ReturnType<typeof setInterval> | null;
  broadcast_unsubscribers: (() => void)[]; // cleanup functions for broadcast listeners
  tracked_puzzles: Set<string>; // puzzles currently being tracked for visibility
  visibility_listener: (() => void) | null; // cleanup function for visibility listener
}

export const usePuzzleProgressStore = defineStore("puzzle.progress", {
  state: (): PuzzleProgressState => ({
    initialized: false,
    definitions: {},
    timestamp_start: {},
    timestamp_finish: {},
    current_puzzle_states: {},
    used_tutorial: {},
    gutter_markings: {},
    displayPrecision: "seconds",
    updateInterval: null,
    broadcast_unsubscribers: [],
    tracked_puzzles: new Set(),
    visibility_listener: null,
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

    /** gets the current puzzle definition for a puzzle type, or null if none */
    get_definition:
      (state) =>
      <T = any>(puzzle_type: string): PuzzleDefinition<T> | null =>
        (state.definitions[puzzle_type] as PuzzleDefinition<T>) ?? null,

    /** gets the current puzzle id for a puzzle type, or null if none */
    get_puzzle_id:
      (state) =>
      (puzzle_type: string): string | null =>
        state.definitions[puzzle_type]?.id ?? null,

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
        if (game.definition) this.definitions[game.id] = game.definition;
        if (game.timestamp_start) this.timestamp_start[game.id] = game.timestamp_start;
        if (game.timestamp_finish) this.timestamp_finish[game.id] = game.timestamp_finish;
        if (game.state) this.current_puzzle_states[game.id] = game.state;
        if (game.used_tutorial) this.used_tutorial[game.id] = game.used_tutorial;
        if (game.gutter_markings) this.gutter_markings[game.id] = game.gutter_markings;
      }

      this.setup_broadcast_listeners();
      this.initialized = true;
    },

    /** sets the active puzzle definition for a puzzle type */
    set_definition(puzzle_type: string, definition: PuzzleDefinition) {
      this.definitions[puzzle_type] = definition;
      databaseManager.progress.update(puzzle_type, { definition: JSON.parse(JSON.stringify(definition)) });
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
      delete this.gutter_markings[puzzle_type]; // reset gutter markings

      await databaseManager.progress.update(puzzle_type, {
        timestamp_start: this.timestamp_start[puzzle_type],
        timestamp_finish: null,
        state: JSON.parse(JSON.stringify(initial_state)),
        used_tutorial: false,
        gutter_markings: null,
      });
      broadcast_channel_service.broadcast_game_reset(puzzle_type, initial_state);

      // start tracking visibility for this puzzle
      await this.start_visibility_tracking(puzzle_type, "freeplay");
    },

    /** marks puzzle as completed with current timestamp */
    async mark_puzzle_solved(puzzle_type: string) {
      this.timestamp_finish[puzzle_type] = Date.now();
      databaseManager.progress.update(puzzle_type, {
        timestamp_finish: this.timestamp_finish[puzzle_type],
      });
      broadcast_channel_service.broadcast_game_solved(puzzle_type, this.timestamp_finish[puzzle_type]);

      // stop tracking visibility for this puzzle
      await this.stop_visibility_tracking(puzzle_type, "freeplay");

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

    /** updates gutter markings for a puzzle */
    async update_gutter_markings(puzzle_type: string, markings: GutterMarkings) {
      this.gutter_markings[puzzle_type] = markings;
      await databaseManager.progress.update(puzzle_type, {
        gutter_markings: JSON.parse(JSON.stringify(markings)),
      });
      broadcast_channel_service.broadcast_gutter_markings_update(puzzle_type, markings);
    },

    /** resets gutter markings for a puzzle */
    async reset_gutter_markings(puzzle_type: string) {
      delete this.gutter_markings[puzzle_type];
      await databaseManager.progress.update(puzzle_type, {
        gutter_markings: null,
      });
      broadcast_channel_service.broadcast_gutter_markings_reset(puzzle_type);
    },

    /** starts tracking page visibility for a puzzle */
    async start_visibility_tracking(puzzle_type: string, mode: "freeplay" | "experiment" = "freeplay") {
      if (this.tracked_puzzles.has(puzzle_type)) {
        log("Already tracking visibility for %s", puzzle_type);
        return;
      }

      this.tracked_puzzles.add(puzzle_type);

      // set up the visibility listener if not already set up
      if (this.visibility_listener === null) {
        this.setup_visibility_listener();
      }

      // record initial visibility state
      emitter.emit("puzzle:visibility-changed", { puzzle_type, mode, visible: !document.hidden });
    },

    /** stops tracking page visibility for a puzzle */
    async stop_visibility_tracking(puzzle_type: string, mode: "freeplay" | "experiment" = "freeplay") {
      if (!this.tracked_puzzles.has(puzzle_type)) {
        return;
      }

      // record final visibility state
      if (!document.hidden) {
        emitter.emit("puzzle:visibility-changed", { puzzle_type, mode, visible: false });
      }

      this.tracked_puzzles.delete(puzzle_type);

      // clean up listener if no more puzzles are being tracked
      if (this.tracked_puzzles.size === 0 && this.visibility_listener !== null) {
        this.visibility_listener();
        this.visibility_listener = null;
      }
    },

    /** sets up the page visibility API listener */
    setup_visibility_listener() {
      const handle_visibility_change = () => {
        const is_visible = !document.hidden;
        for (const puzzle_type of this.tracked_puzzles) {
          emitter.emit("puzzle:visibility-changed", { puzzle_type, mode: "freeplay", visible: is_visible });
        }
      };

      document.addEventListener("visibilitychange", handle_visibility_change);

      // return cleanup function
      this.visibility_listener = () => {
        document.removeEventListener("visibilitychange", handle_visibility_change);
      };
    },

    /** setup broadcast channel listeners for cross-tab sync */
    setup_broadcast_listeners() {
      log("Setting up broadcast listeners");
      // listen for game state updates from other tabs
      this.broadcast_unsubscribers.push(
        broadcast_channel_service.subscribe('game_state_update', (message) => {
          log("Received game state update via broadcast: %O", message);
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

      // listen for gutter markings updates from other tabs
      this.broadcast_unsubscribers.push(
        broadcast_channel_service.subscribe('gutter_markings_update', (message) => {
          this.gutter_markings[message.puzzle_type] = message.data.markings;
        })
      );

      // listen for gutter markings reset from other tabs
      this.broadcast_unsubscribers.push(
        broadcast_channel_service.subscribe('gutter_markings_reset', (message) => {
          delete this.gutter_markings[message.puzzle_type];
        })
      );

      // listen for new puzzle loaded from other tabs
      this.broadcast_unsubscribers.push(
        broadcast_channel_service.subscribe('new_puzzle', (message) => {
          this.definitions[message.puzzle_type] = message.data.puzzle_definition;
          this.current_puzzle_states[message.puzzle_type] = message.data.puzzle_definition.initial_state;
          delete this.used_tutorial[message.puzzle_type];
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
