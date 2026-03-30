/**
 * usePlayback — fetches attempt data and provides canvas state.
 * accepts shared playback controls so multiple instances can be synced.
 */

import { ref, computed, onMounted, type Ref } from "vue";
import { ACTIVE_GAMES } from "@/constants";
import type { PlaybackFrame } from "@/core/types";
import { usePlaybackControls } from "./usePlaybackControls";

export function usePlayback(
  attempt_id: string,
  shared_controls?: ReturnType<typeof usePlaybackControls>,
) {
  const loading = ref(true);
  const error = ref<string | null>(null);
  const puzzle_definition = ref<any>(null);
  const frames = ref<PlaybackFrame[]>([]);
  const timestamp_start = ref(0);
  const is_solved = ref(false);

  // use shared controls or create own
  const controls = shared_controls ?? usePlaybackControls(() => frames.value.length);

  // fetch attempt data
  onMounted(async () => {
    try {
      const res = await fetch(`/api/puzzle/freeplay/attempts/${attempt_id}`, {
        credentials: "include",
      });
      if (!res.ok) {
        error.value = `failed to load: ${res.status}`;
        return;
      }
      const data = await res.json();
      puzzle_definition.value = data.puzzle_definition;
      frames.value = data.frames;
      timestamp_start.value = data.timestamp_start;
      is_solved.value = data.is_solved;
    } catch (e) {
      error.value = "failed to load attempt";
    } finally {
      loading.value = false;
    }
  });

  // derived state
  const puzzle_type = computed(() => puzzle_definition.value?.puzzle_type ?? "");
  const canvas_component = computed(() => ACTIVE_GAMES[puzzle_type.value]?.component ?? null);

  // clamp to this attempt's frame count
  const clamped_frame = computed(() =>
    Math.min(controls.current_frame.value, frames.value.length - 1)
  );

  const canvas_state = computed(() => {
    if (!puzzle_definition.value || frames.value.length === 0) return null;
    const frame = frames.value[clamped_frame.value];
    if (!frame) return null;
    return {
      definition: puzzle_definition.value,
      board: frame.board,
      violations: [],
      solved: false,
    };
  });

  // time gaps between moves (ms)
  const move_delays = computed(() => {
    const f = frames.value;
    if (f.length < 2) return [];
    const delays: number[] = [];
    for (let i = 1; i < f.length; i++) {
      const prev_ts = i === 1 ? timestamp_start.value : f[i - 1].timestamp;
      delays.push(Math.max(0, f[i].timestamp - prev_ts));
    }
    return delays;
  });

  return {
    // data
    loading,
    error,
    puzzle_definition,
    frames,
    timestamp_start,
    is_solved,
    puzzle_type,
    canvas_component,
    canvas_state,
    move_delays,
    clamped_frame,

    // controls (shared or own)
    controls,
  };
}
