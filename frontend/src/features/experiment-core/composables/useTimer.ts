import { onUnmounted, ref } from "vue";

export function useTimer({ duration_seconds = 60 } = {}) {
  const time_remaining = ref(duration_seconds);
  let timer_interval: NodeJS.Timeout | null = null;

  // overload signatures
  function start(onComplete: () => void): void;
  function start(duration: number, onComplete: () => void): void;

  // implementation
  function start(durationOrCallback: number | (() => void), onComplete?: () => void): void {
    stop(); // clear any existing timer

    let duration: number;
    let callback: () => void;

    if (typeof durationOrCallback === "function") {
      // start(onComplete) - use default duration
      duration = duration_seconds;
      callback = durationOrCallback;
    } else {
      // start(duration, onComplete)
      duration = durationOrCallback;
      callback = onComplete!;
    }

    time_remaining.value = duration;

    timer_interval = setInterval(() => {
      if (time_remaining.value > 1) {
        time_remaining.value--;
      } else {
        stop();
        callback();
      }
    }, 1000);
  }

  function stop() {
    if (timer_interval) {
      clearInterval(timer_interval);
      timer_interval = null;
    }
  }

  function reset() {
    stop();
    time_remaining.value = 0;
  }

  // Cleanup on unmount
  onUnmounted(() => {
    stop();
  });

  return {
    time_remaining,
    start,
    stop,
    reset,
  };
}
