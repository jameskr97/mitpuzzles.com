import { format_game_stopwatch } from "@/services/util.ts";

/** Simplifies resetting all of localStorage through a version variable. */
export class StorageVersionManager {
  // Change this to current date when updating the storage version
  private static readonly VERSION = "2025-05-02";
  static clearOldStorage() {
    const saved = localStorage.getItem("mitlogic.storageVersion");
    if (saved !== StorageVersionManager.VERSION) {
      Object.keys(localStorage).forEach((key) => {
        if (key === "mitlogic.storageVersion") return;
        if (key.startsWith("mitlogic")) {
          localStorage.removeItem(key);
        }
      });
      localStorage.setItem("mitlogic.storageVersion", StorageVersionManager.VERSION);
    }
  }
}

import { computed, type ComputedRef, ref, type Ref } from "vue";
import logger from "@/services/logger.ts";

export class PuzzleTimer {
  private timer_id: ReturnType<typeof setInterval> | null = null;

  public elapsed_ms: Ref<number> = ref(0);
  public time_completed: Ref<boolean> = ref(false);
  public display_time: ComputedRef<string> = computed(() => format_game_stopwatch(this.elapsed_ms.value));

  constructor(elapsed_ms: Ref<number>, time_completed: Ref<boolean>) {
    this.elapsed_ms = elapsed_ms;
    this.time_completed = time_completed;
    if (!this.time_completed.value) {
      this.start();
    }
  }

  public reset() {
    this.stop();
    this.elapsed_ms.value = 0;
    this.time_completed.value = false;
  }

  public start() {
    if (this.timer_id != null) return;
    if (this.time_completed.value) return;
    logger.debug("Timer started");

    this.timer_id = setInterval(() => {
      this.elapsed_ms.value += 1000
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
    this.time_completed.value = true
  }
}
