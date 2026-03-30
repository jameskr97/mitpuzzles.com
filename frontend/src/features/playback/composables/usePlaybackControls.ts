/**
 * usePlaybackControls — owns playback position and timer.
 * shared across multiple playback data sources.
 */

import { ref, computed, onUnmounted } from "vue";

export function usePlaybackControls(total_frames: () => number) {
  const current_frame = ref(0);
  const is_playing = ref(false);
  const moves_per_second = ref(5);
  let timer_id: ReturnType<typeof setTimeout> | null = null;

  function clear_timer() {
    if (timer_id !== null) { clearTimeout(timer_id); timer_id = null; }
  }

  function schedule_next() {
    const total = total_frames();
    if (!is_playing.value || current_frame.value >= total - 1) {
      is_playing.value = false;
      return;
    }
    timer_id = setTimeout(() => {
      current_frame.value++;
      schedule_next();
    }, 1000 / moves_per_second.value);
  }

  function toggle_play() {
    if (is_playing.value) {
      is_playing.value = false;
      clear_timer();
    } else {
      const total = total_frames();
      if (current_frame.value >= total - 1) current_frame.value = 0;
      is_playing.value = true;
      schedule_next();
    }
  }

  function seek(frame: number) {
    is_playing.value = false;
    clear_timer();
    current_frame.value = Math.max(0, Math.min(total_frames() - 1, frame));
  }

  function set_mps(mps: number) {
    moves_per_second.value = mps;
    if (is_playing.value) { clear_timer(); schedule_next(); }
  }

  onUnmounted(clear_timer);

  return {
    current_frame,
    is_playing,
    moves_per_second,
    toggle_play,
    seek,
    set_mps,
  };
}
