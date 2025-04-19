import { format_game_stopwatch } from "@/services/util.ts";

/** Simplifies resetting all of localStorage through a version variable. */
export class StorageVersionManager {
  // Change this to current date when updating the storage version
  private static readonly VERSION = "2025-04-18";
  static clearOldStorage() {
    const saved = localStorage.getItem("mitlogic.storageVersion");
    if (saved !== StorageVersionManager.VERSION) {
      Object.keys(localStorage).forEach((key) => {
        if (key.startsWith("mitlogic.puzzles:")) {
          localStorage.removeItem(key);
        }
      });
      localStorage.setItem("mitlogic.storageVersion", StorageVersionManager.VERSION);
    }
  }
}

// src/services/PuzzleTimer.ts
import { computed, type ComputedRef, ref, type Ref } from "vue";
import logger from "@/services/logger.ts";

export class PuzzleTimer {
  private timer_id: ReturnType<typeof setInterval> | null = null;

  public time_started: Ref<number> = ref(0);
  public elapsed_ms: Ref<number> = ref(0);
  public completed_ms: Ref<number> = ref(-1);
  public display_time: ComputedRef<string> = computed(() => format_game_stopwatch(this.elapsed_ms.value));

  constructor(time_started: Ref<number>, time_completed: Ref<number>) {
    // bind storage refs
    this.time_started.value = time_started.value;
    this.completed_ms = time_completed;
    // initialize elapsed time from stored values
    if (this.completed_ms.value >= 0) {
      // already completed
      this.elapsed_ms.value = this.completed_ms.value;
    } else if (this.time_started.value > 0) {
      // resuming in-progress timer
      this.elapsed_ms.value = Date.now() - this.time_started.value;
      this.start();
    }
  }

  public reset() {
    this.stop();
    this.time_started.value = 0;
    this.elapsed_ms.value = 0;
    this.completed_ms.value = -1;
  }

  public start() {
    if (this.timer_id != null) return;
    logger.debug("Timer started");

    this.timer_id = setInterval(() => {
      this.elapsed_ms.value = Date.now() - this.time_started.value!;
    }, 1000);
  }

  public stop() {
    if (this.timer_id == null) return;
    logger.debug("Timer stopped");
    clearInterval(this.timer_id);
    this.timer_id = null;
  }

  public complete() {
    logger.debug("Timer marked complete");
    this.stop();
    this.completed_ms.value = this.elapsed_ms.value;
  }
}
