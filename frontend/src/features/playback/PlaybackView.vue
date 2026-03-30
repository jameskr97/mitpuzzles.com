<script setup lang="ts">
/** PlaybackView — renders puzzle attempt replay with timeline and timing chart */
import { computed } from "vue";
import { Bar } from "vue-chartjs";
import {
  Chart as ChartJS, CategoryScale, LinearScale, BarElement, Tooltip,
} from "chart.js";
import zoomPlugin from "chartjs-plugin-zoom";
import Container from "@/core/components/ui/Container.vue";
import PlaybackTimeline from "./components/PlaybackTimeline.vue";
import { usePlayback } from "./composables/usePlayback";

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, zoomPlugin);

const props = defineProps<{
  attempt_id: string;
}>();

const pb = usePlayback(props.attempt_id);
const { controls } = pb;

// chart data
const chart_data = computed(() => ({
  labels: pb.move_delays.value.map((_, i) => `${i + 1}`),
  datasets: [{
    data: pb.move_delays.value,
    backgroundColor: pb.move_delays.value.map((_, i) =>
      i + 1 === controls.current_frame.value ? "#2563eb" : "#93c5fd"
    ),
    borderRadius: 2,
    minBarLength: 4,
  }],
}));

const chart_options = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: {
      callbacks: {
        label: (ctx: any) => `${Math.round(ctx.parsed.y)}ms`,
      },
    },
    zoom: {
      pan: { enabled: true, mode: "x" as const },
      zoom: { wheel: { enabled: true }, pinch: { enabled: true }, mode: "x" as const },
    },
  },
  scales: {
    y: {
      title: { display: true, text: "ms", font: { size: 10 } },
      beginAtZero: true,
      ticks: { callback: (value: any) => `${Math.round(Number(value))}` },
    },
    x: { display: false },
  },
  onClick: (_event: any, elements: any[]) => {
    if (elements.length > 0) controls.seek(elements[0].index + 1);
  },
};
</script>

<template>
  <div class="flex flex-col gap-3 max-w-md mx-auto mt-4">

    <Container v-if="pb.loading.value" class="flex justify-center py-20">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
    </Container>

    <Container v-else-if="pb.error.value" class="text-center py-20">
      <p class="text-gray-500">{{ pb.error.value }}</p>
    </Container>

    <template v-else-if="pb.canvas_state.value">

      <!-- canvas -->
      <Container class="aspect-square pointer-events-none select-none">
        <component
          v-if="pb.canvas_component.value"
          :is="pb.canvas_component.value"
          :state="pb.canvas_state.value"
        />
      </Container>

      <!-- timeline -->
      <Container>
        <PlaybackTimeline
          :frames="pb.frames.value"
          :current_frame="controls.current_frame.value"
          :is_playing="controls.is_playing.value"
          :moves_per_second="controls.moves_per_second.value"
          @seek="controls.seek"
          @toggle-play="controls.toggle_play"
          @set-mps="controls.set_mps"
        />
      </Container>

      <!-- time between moves chart -->
      <Container>
        <div class="text-xs text-gray-400 mb-1">time between moves</div>
        <div class="h-24">
          <Bar :data="chart_data" :options="chart_options" />
        </div>
      </Container>

    </template>
  </div>
</template>
