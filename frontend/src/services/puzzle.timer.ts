import { computed, ref, watch, type ComputedRef, type Ref } from "vue";
import { format_game_stopwatch } from "./util";

export class PuzzleTimer {
  private intervalId: number | null = null;

  private time_started: Ref<number>;
  private time_completed: Ref<number | undefined>;
  time_elapsed: Ref<number>;
  display_time: ComputedRef<string>;

  constructor(time_started: Ref<number>, time_completed: Ref<number | undefined>) {
    this.intervalId = null;
    this.time_started = time_started;
    this.time_completed = time_completed;
    this.time_elapsed = ref(0);
    this.display_time = computed(() => format_game_stopwatch(this.time_elapsed.value));

    this.updateScreenTime();
    watch(
      [this.time_started, this.time_completed],
      () => {
        if (this.time_completed.value === undefined) {
          this.updateScreenTime();
          if (this.intervalId === null) {
            this.intervalId = setInterval(this.updateScreenTime, 1000);
          }
        } else {
          this.clearInterval();
          this.updateScreenTime();
        }
      },
      { immediate: true },
    );
  }

  complete() {
    if (this.time_completed.value == null) {
      this.time_completed.value = Date.now();
    }

    this.updateScreenTime();
    this.clearInterval();
  }

  clearInterval() {
    if (this.intervalId !== null) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
  }

  reset() {
    this.time_started.value = Date.now();
    this.time_completed.value = undefined;
    this.time_elapsed.value = 0;
  }

  updateScreenTime = () => {
    if (this.time_completed.value !== undefined) {
      this.time_elapsed.value = this.time_completed.value - this.time_started.value;
    } else {
      this.time_elapsed.value = Date.now() - this.time_started.value;
    }
  };
}
