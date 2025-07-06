import { defineStore } from "pinia";
import { ACTIVE_GAMES } from "@/constants.ts";
import { databaseManager } from "@/store/database";

export const useGameAttemptStore = defineStore("game.attempt", {
  state: () => ({
    initialized: false,
    times: {} as Record<string, number>,
    solvedStatus: {} as Record<string, boolean>,
    completion_duration_ms: {} as Record<string, number | null>,
    completion_datetime: {} as Record<string, number | null>,
    displayPrecision: "seconds" as "seconds" | "milliseconds",
    activeTimers: {} as Record<
      string,
      {
        startTime: number;
        isRunning: boolean;
        lastSaveTime: number;
      }
    >,
    saveInterval: null as NodeJS.Timeout | null,
    updateInterval: null as NodeJS.Timeout | null,
    performanceOrigin: performance.timeOrigin,
    lastUpdateTime: 0,
    SAVE_INTERVAL_MS: 5000,
    UPDATE_INTERVAL_MS: 100,
  }),

  getters: {
    getTime:
      (state) =>
      (puzzle_type: string): number => {
        const activeTimer = state.activeTimers[puzzle_type];
        if (activeTimer?.isRunning) {
          state.lastUpdateTime; // Force reactivity
          const currentElapsed = performance.now() - activeTimer.startTime;
          return (state.times[puzzle_type] || 0) + currentElapsed;
        }
        return state.times[puzzle_type] || 0;
      },

    getTimeInSeconds(state): (puzzle_type: string) => number {
      return (puzzle_type: string): number => {
        return this.getTime(puzzle_type) / 1000;
      };
    },

    getFormattedTime(state): (puzzle_type: string, precision?: "seconds" | "milliseconds") => string {
      return (puzzle_type: string, precision?: "seconds" | "milliseconds"): string => {
        let totalMs;
        if (this.isPuzzleSolved(puzzle_type) && this.completion_duration_ms[puzzle_type] !== null) {
          totalMs = this.completion_duration_ms[puzzle_type];
        } else {
          totalMs = this.getTime(puzzle_type);
        }

        const minutes = Math.floor(totalMs / 60000);
        const seconds = Math.floor((totalMs % 60000) / 1000);
        const milliseconds = Math.floor(totalMs % 1000);

        const usePrecision = precision || state.displayPrecision;

        if (usePrecision === "milliseconds") {
          return `${minutes.toString().padStart(2, "0")}:${seconds.toString().padStart(2, "0")}.${milliseconds.toString().padStart(3, "0")}`;
        } else {
          return `${minutes.toString().padStart(2, "0")}:${seconds.toString().padStart(2, "0")}`;
        }
      };
    },

    isRunning:
      (state) =>
      (puzzle_type: string): boolean => {
        return state.activeTimers[puzzle_type]?.isRunning;
      },

    hasRunningTimers: (state) => (): boolean => {
      return Object.values(state.activeTimers).some((timer) => timer.isRunning);
    },

    getAllTimes: (state) => (): Record<string, number> => {
      const result = { ...state.times };
      Object.keys(state.activeTimers).forEach((puzzle_type) => {
        const timer = state.activeTimers[puzzle_type];
        if (timer.isRunning) {
          const currentElapsed = performance.now() - timer.startTime;
          result[puzzle_type] = (state.times[puzzle_type] || 0) + currentElapsed;
        }
      });
      return result;
    },

    isPuzzleSolved:
      (state) =>
      (puzzle_type: string): boolean => {
        return state.solvedStatus[puzzle_type] || false;
      },

    getCompletionDuration:
      (state) =>
      (puzzle_type: string): number | null => {
        return state.completion_duration_ms[puzzle_type] || null;
      },

    getCompletionDatetime:
      (state) =>
      (puzzle_type: string): Date | null => {
        return state.completion_datetime[puzzle_type] || null;
      },

    getAllSolvedStatus: (state) => (): Record<string, boolean> => {
      return { ...state.solvedStatus };
    },
  },

  actions: {
    async initializeStore() {
      if (this.initialized) return;

      try {
        // Initialize database manager
        await databaseManager.init();

        // Load all attempt data from database
        const allAttempts = await databaseManager.attempts.getAllPuzzleAttempts();

        // Populate reactive state
        for (const [puzzle_type, attempt] of Object.entries(allAttempts)) {
          this.times[puzzle_type] = attempt.solving_time;
          this.solvedStatus[puzzle_type] = attempt.solved;
          this.completion_duration_ms[puzzle_type] = attempt.completion_duration_ms;
          this.completion_datetime[puzzle_type] = attempt.completed_at ? new Date(attempt.completed_at) : null;
        }

        // Initialize missing puzzle types
        for (const puzzle_type of Object.keys(ACTIVE_GAMES)) {
          if (this.times[puzzle_type] === undefined) {
            this.times[puzzle_type] = 0;
            this.solvedStatus[puzzle_type] = false;
            this.completion_duration_ms[puzzle_type] = null;
            this.completion_datetime[puzzle_type] = null;
            await databaseManager.attempts.updatePuzzleAttempt(puzzle_type, { solving_time: 0 });
          }
        }

        // Start periodic save and reactive updates
        this.startPeriodicSave();
        this.startReactiveUpdates();

        this.initialized = true;
        console.log(`Attempt store initialized`);
      } catch (error) {
        console.error("Failed to initialize attempt store:", error);
        this.initialized = false;
      }
    },

    // ... rest of the timer methods remain the same ...
    startTimer(puzzle_type: string) {
      if (this.isPuzzleSolved(puzzle_type)) return;

      const now = performance.now();
      if (!this.activeTimers[puzzle_type]) {
        this.activeTimers[puzzle_type] = {
          startTime: now,
          isRunning: true,
          lastSaveTime: now,
        };
      } else {
        this.activeTimers[puzzle_type].startTime = now;
        this.activeTimers[puzzle_type].isRunning = true;
        this.activeTimers[puzzle_type].lastSaveTime = now;
      }

      this.startReactiveUpdates();
    },

    pauseTimer(puzzle_type: string) {
      const timer = this.activeTimers[puzzle_type];
      if (timer?.isRunning) {
        const now = performance.now();
        const elapsed = now - timer.startTime;
        this.times[puzzle_type] = (this.times[puzzle_type] || 0) + elapsed;
        timer.isRunning = false;

        this.saveTimer(puzzle_type);

        if (!this.hasRunningTimers()) {
          this.stopReactiveUpdates();
        }
      }
    },

    stopTimer(puzzle_type: string) {
      this.pauseTimer(puzzle_type);
      delete this.activeTimers[puzzle_type];
    },

    async saveTimer(puzzle_type: string) {
      const currentTime = this.getTime(puzzle_type);

      try {
        await databaseManager.attempts.updatePuzzleAttempt(puzzle_type, {
          solving_time: Math.round(currentTime),
        });

        if (this.activeTimers[puzzle_type]) {
          this.activeTimers[puzzle_type].lastSaveTime = performance.now();
        }
      } catch (error) {
        console.warn(`Failed to save timer for ${puzzle_type}:`, error);
      }
    },

    async resetPuzzleProgress(puzzle_type: string) {
      this.times[puzzle_type] = 0;
      this.solvedStatus[puzzle_type] = false;
      this.completion_duration_ms[puzzle_type] = null;
      this.completion_datetime[puzzle_type] = null;
      delete this.activeTimers[puzzle_type];

      try {
        await databaseManager.attempts.resetPuzzleAttempt(puzzle_type);
      } catch (error) {
        console.warn(`Failed to reset puzzle progress for ${puzzle_type}:`, error);
      }
    },

    async markPuzzleSolved(puzzle_type: string) {
      const completion_datetime = Date.now();
      const finalCompletionTime = this.getTime(puzzle_type);

      this.solvedStatus[puzzle_type] = true;
      this.completion_duration_ms[puzzle_type] = Math.trunc(finalCompletionTime);
      this.completion_datetime[puzzle_type] = completion_datetime;

      await databaseManager.attempts.updatePuzzleAttempt(puzzle_type, {
        solved: true,
        completion_duration_ms: this.completion_duration_ms[puzzle_type],
        completed_at: this.completion_datetime[puzzle_type],
      });

      this.stopTimer(puzzle_type);
    },

    startPeriodicSave() {
      if (this.saveInterval) {
        clearInterval(this.saveInterval);
      }

      this.saveInterval = setInterval(async () => {
        const runningTimers = Object.keys(this.activeTimers).filter(
          (puzzle_type) => this.activeTimers[puzzle_type].isRunning,
        );

        if (runningTimers.length > 0) {
          for (const puzzle_type of runningTimers) {
            await this.saveTimer(puzzle_type);
          }
        }
      }, this.SAVE_INTERVAL_MS);
    },

    stopPeriodicSave() {
      if (this.saveInterval) {
        clearInterval(this.saveInterval);
        this.saveInterval = null;
      }
    },

    startReactiveUpdates() {
      if (this.updateInterval) {
        return;
      }

      this.updateInterval = setInterval(() => {
        const hasRunningTimers = Object.values(this.activeTimers).some((timer) => timer.isRunning);

        if (hasRunningTimers) {
          this.lastUpdateTime = performance.now();
        } else {
          this.stopReactiveUpdates();
        }
      }, this.UPDATE_INTERVAL_MS);
    },

    stopReactiveUpdates() {
      if (this.updateInterval) {
        clearInterval(this.updateInterval);
        this.updateInterval = null;
      }
    },

    setShowMilliseconds(show_ms: true) {
      this.displayPrecision = show_ms ? "milliseconds" : "seconds";
    },
  },
});
