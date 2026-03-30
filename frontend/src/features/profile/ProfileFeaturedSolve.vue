<script setup lang="ts">
import Container from "@/core/components/ui/Container.vue";
import PlaybackTimeline from "@/features/playback/components/PlaybackTimeline.vue";
import type { PlaybackFrame } from "@/core/types";
import type { usePlaybackControls } from "@/features/playback/composables/usePlaybackControls";

const props = defineProps<{
  puzzle_type: string;
  best_time: number;
  frames: PlaybackFrame[];
  canvas_component: any;
  canvas_state: any;
  controls: ReturnType<typeof usePlaybackControls>;
}>();

function capitalize(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

function format_time(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, "0")}`;
}
</script>

<template>
  <Container>
    <div class="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">
      Fastest {{ capitalize(puzzle_type) }} — {{ format_time(best_time) }}
    </div>
    <div class="flex flex-col gap-2 flex-1">
      <div class="w-full overflow-hidden pointer-events-none select-none">
        <component
          v-if="canvas_component && canvas_state?.value"
          :is="canvas_component"
          :state="canvas_state.value"
        />
      </div>
      <div class="flex-1" />
      <PlaybackTimeline
        v-if="frames.length > 0"
        :frames="frames"
        :current_frame="controls.current_frame.value"
        :is_playing="controls.is_playing.value"
        :moves_per_second="controls.moves_per_second.value"
        size="small"
        @seek="controls.seek"
        @toggle-play="controls.toggle_play"
        @set-mps="controls.set_mps"
      />
      <div v-else class="text-xs text-gray-400 italic">playback data not available</div>
    </div>
  </Container>
</template>
