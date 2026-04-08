<script setup lang="ts">
import { ref, computed } from "vue";
import Container from "@/core/components/ui/Container.vue";
import ConfigurableChart from "@/features/graphs/components/ConfigurableChart.vue";
import type { ChartFeature, ChartSeries } from "@/features/graphs/components/ConfigurableChart.vue";
import { ACTIVE_GAMES } from "@/constants";

const CHART_COLORS: Record<string, string> = {
  sudoku: "#3b82f6", nonograms: "#ef4444", minesweeper: "#22c55e",
  lightup: "#f59e0b", hashi: "#8b5cf6", mosaic: "#ec4899",
  tents: "#14b8a6", aquarium: "#06b6d4", kakurasu: "#f97316",
  norinori: "#a855f7", yinyang: "#6366f1",
};

const SMOOTHING_WINDOW = 5;

const props = defineProps<{
  solve_time_history: Record<string, { date: string; avg_time: number }[]>;
}>();

// default: select the type with the most solves
const most_played = Object.entries(props.solve_time_history)
  .sort((a, b) => b[1].length - a[1].length)[0]?.[0];
const visible_types = ref<Set<string>>(most_played ? new Set([most_played]) : new Set());

function toggle_type(puzzle_type: string) {
  const next = new Set(visible_types.value);
  if (next.has(puzzle_type)) next.delete(puzzle_type);
  else next.add(puzzle_type);
  visible_types.value = next;
}

function capitalize(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

function get_game_icon(puzzle_type: string): string {
  return ACTIVE_GAMES[puzzle_type]?.icon ?? "🧩";
}

function format_time(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, "0")}`;
}

/** Rolling average with window size */
function smooth(values: number[], window: number): number[] {
  return values.map((_, i) => {
    const start = Math.max(0, i - window + 1);
    const slice = values.slice(start, i + 1);
    return slice.reduce((a, b) => a + b, 0) / slice.length;
  });
}

const features: ChartFeature[] = [
  { key: "puzzle_number", label: "Puzzle #", type: "number" },
  { key: "solve_time", label: "Solve Time", type: "number", format: format_time },
];

const series = computed<ChartSeries[]>(() =>
  [...visible_types.value].map(type => ({
    key: type,
    label: capitalize(type),
    color: CHART_COLORS[type] ?? "#888",
  }))
);

const points = computed(() => {
  const result: Record<string, any>[] = [];
  for (const type of visible_types.value) {
    const raw = (props.solve_time_history[type] ?? [])
      .filter(p => p.avg_time <= 600)
      .map(p => p.avg_time);
    const smoothed = smooth(raw, SMOOTHING_WINDOW);
    for (let i = 0; i < smoothed.length; i++) {
      result.push({
        puzzle_number: i + 1,
        solve_time: smoothed[i],
        _series: type,
      });
    }
  }
  return result;
});
</script>

<template>
  <Container>
    <div class="flex items-center gap-1 mb-2 flex-wrap">
      <button
        v-for="type in Object.keys(solve_time_history)"
        :key="type"
        class="px-1.5 py-0.5 text-[10px] font-medium rounded border transition-colors"
        :class="visible_types.has(type)
          ? 'text-white border-transparent'
          : 'bg-white text-gray-400 border-gray-200'"
        :style="visible_types.has(type) ? { backgroundColor: CHART_COLORS[type], borderColor: CHART_COLORS[type] } : {}"
        @click="toggle_type(type)"
      >
        {{ get_game_icon(type) }} {{ capitalize(type) }}
      </button>
    </div>
    <div v-if="visible_types.size === 0" class="h-64 flex items-center justify-center text-gray-400 text-sm">
      Select a puzzle type to view solve times
    </div>
    <ConfigurableChart
      v-else
      :points="points"
      :features="features"
      :series="series"
      series-key="_series"
      x="puzzle_number"
      y="solve_time"
      :line="true"
      :tension="0.3"
      :point-radius="2"
      :height="256"
    />
  </Container>
</template>
