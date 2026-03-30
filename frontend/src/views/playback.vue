<script setup lang="ts">
/** admin playback view — multi-attempt test */
import { computed, ref, onMounted } from "vue";
import { ACTIVE_GAMES } from "@/constants";
import Container from "@/core/components/ui/Container.vue";
import PlaybackTimeline from "@/features/playback/components/PlaybackTimeline.vue";
import { usePlaybackControls } from "@/features/playback/composables/usePlaybackControls";
import type { PlaybackFrame } from "@/core/types";

const ATTEMPT_IDS = [
  "019d398e-c73d-75cc-af27-6e3f242c89eb",
  "019d261b-4ce5-708d-9fa7-05b8c32574fc",
  "019d391c-abe3-7bb9-a4a9-7211c73d771d",
  "019d2622-6f65-7e87-9a6b-b9f9fa0b036d",
  "019d38be-c29a-7e67-8f25-4a58ce723497",
  "019cf54b-e504-7bc6-b905-86297d188650",
  "019cf542-43c9-77f4-84b9-1b9953132fc1",
  "019d3b35-5303-7d23-b0ff-740bd283e1a1",
  "019d38bc-b50d-7463-a894-d45cf672135e",
];

interface AttemptData {
  puzzle_definition: any;
  frames: PlaybackFrame[];
  is_solved: boolean;
  puzzle_type: string;
  canvas_component: any;
}

const loading = ref(true);
const error = ref<string | null>(null);
const attempts = ref<AttemptData[]>([]);

// shared controls — total frames = max across all attempts
const controls = usePlaybackControls(() =>
  Math.max(...attempts.value.map(a => a.frames.length), 1)
);

onMounted(async () => {
  try {
    const results = await Promise.all(
      ATTEMPT_IDS.map(async (id) => {
        const res = await fetch(`/api/puzzle/freeplay/attempts/${id}`, { credentials: "include" });
        if (!res.ok) throw new Error(`failed: ${id}`);
        return res.json();
      })
    );

    attempts.value = results.map((data) => {
      const puzzle_type = data.puzzle_definition?.puzzle_type ?? "";
      return {
        puzzle_definition: data.puzzle_definition,
        frames: data.frames,
        is_solved: data.is_solved,
        puzzle_type,
        canvas_component: ACTIVE_GAMES[puzzle_type]?.component ?? null,
      };
    });
  } catch (e: any) {
    error.value = e.message ?? "failed to load attempts";
  } finally {
    loading.value = false;
  }
});

function get_canvas_state(attempt: AttemptData) {
  if (!attempt.frames.length) return null;
  const frame_idx = Math.min(controls.current_frame.value, attempt.frames.length - 1);
  const frame = attempt.frames[frame_idx];
  if (!frame) return null;
  return {
    definition: attempt.puzzle_definition,
    board: frame.board,
    violations: [],
    solved: false,
  };
}

// timeline uses the longest frame list
const max_frames = computed(() => {
  let longest: PlaybackFrame[] = [];
  for (const a of attempts.value) {
    if (a.frames.length > longest.length) longest = a.frames;
  }
  return longest;
});
</script>

<template>
  <div class="flex flex-col gap-4 mx-auto mt-4 px-4">

    <Container v-if="loading" class="flex justify-center py-20">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
    </Container>

    <Container v-else-if="error" class="text-center py-20">
      <p class="text-gray-500">{{ error }}</p>
    </Container>

    <template v-else>

      <!-- grid of canvases -->
      <div class="grid grid-cols-3 gap-3">
        <div v-for="(attempt, i) in attempts" :key="i" class="flex flex-col gap-1">
          <div class="text-xs text-gray-400 truncate">
            {{ attempt.puzzle_type }} {{ attempt.puzzle_definition?.puzzle_size }}
          </div>
          <div class="aspect-square pointer-events-none select-none border border-gray-100 rounded">
            <component
              v-if="attempt.canvas_component && get_canvas_state(attempt)"
              :is="attempt.canvas_component"
              :state="get_canvas_state(attempt)"
            />
          </div>
          <div class="text-[10px] text-gray-300 text-center">
            {{ Math.min(controls.current_frame.value, attempt.frames.length - 1) }} / {{ attempt.frames.length - 1 }}
          </div>
        </div>
      </div>

      <!-- shared timeline -->
      <Container>
        <PlaybackTimeline
          :frames="max_frames"
          :current_frame="controls.current_frame.value"
          :is_playing="controls.is_playing.value"
          :moves_per_second="controls.moves_per_second.value"
          @seek="controls.seek"
          @toggle-play="controls.toggle_play"
          @set-mps="controls.set_mps"
        />
      </Container>

    </template>
  </div>
</template>
