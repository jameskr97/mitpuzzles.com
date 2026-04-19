<script setup lang="ts">
import { ref, computed } from "vue";
import Container from "@/core/components/ui/Container.vue";
import ConfigurableChart from "@/features/graphs/components/ConfigurableChart.vue";
import PuzzleTypeSelector from "@/features/graphs/components/PuzzleTypeSelector.vue";
import { Popover, PopoverTrigger, PopoverContent } from "@/core/components/ui/popover";
import type { ChartFeature, ChartSeries } from "@/features/graphs/components/ConfigurableChart.vue";

const CHART_COLORS: Record<string, string> = {
  sudoku: "#3b82f6", nonograms: "#ef4444", minesweeper: "#22c55e",
  lightup: "#f59e0b", hashi: "#8b5cf6", mosaic: "#ec4899",
  tents: "#14b8a6", aquarium: "#06b6d4", kakurasu: "#f97316",
  norinori: "#a855f7", yinyang: "#6366f1",
};

const smoothing_window = ref(5);
const custom_input = ref("");

const props = defineProps<{
  solve_time_history: Record<string, { date: string; avg_time: number }[]>;
}>();

const history = ref<Record<string, { date: string; avg_time: number }[]>>({ ...props.solve_time_history });
const site_averages = ref<Record<string, number>>({});
const loading = ref(false);

async function on_filter_update(filters: { puzzle_type: string; puzzle_size: string; puzzle_difficulty: string }) {
  if (!filters.puzzle_type) {
    history.value = { ...props.solve_time_history };
    site_averages.value = {};
    return;
  }

  loading.value = true;
  try {
    const params = new URLSearchParams();
    if (filters.puzzle_type) params.append("puzzle_type", filters.puzzle_type);
    if (filters.puzzle_size) params.append("puzzle_size", filters.puzzle_size);
    if (filters.puzzle_difficulty) params.append("puzzle_difficulty", filters.puzzle_difficulty);

    const res = await fetch(`/api/me/solve-history?${params}`, { credentials: "include" });
    if (!res.ok) return;
    const data: { puzzle_type: string; data: { date: string; avg_time: number }[] }[] = await res.json();

    const result: Record<string, { date: string; avg_time: number }[]> = {};
    for (const series of data) {
      result[series.puzzle_type] = series.data;
    }
    history.value = result;

    const avg_res = await fetch(`/api/me/site-average?${params}`, { credentials: "include" });
    if (avg_res.ok) site_averages.value = await avg_res.json();
  } finally {
    loading.value = false;
  }
}

const visible_types = computed(() => new Set(Object.keys(history.value)));

function capitalize(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

function format_time(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, "0")}`;
}

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

const reference_lines = computed(() =>
  Object.entries(site_averages.value).map(([type, avg]) => ({
    value: avg,
    label: `${capitalize(type)} avg`,
    color: "#9ca3af",
    dash: "6,3",
  }))
);

const points = computed(() => {
  const result: Record<string, any>[] = [];
  for (const type of visible_types.value) {
    const raw = (history.value[type] ?? [])
      .filter(p => p.avg_time <= 600)
      .map(p => p.avg_time);
    const smoothed = smooth(raw, smoothing_window.value);
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
    <div class="flex items-center gap-2 mb-2">
      <Popover>
        <PopoverTrigger
          class="text-[10px] px-1.5 py-0.5 rounded border transition-colors shrink-0"
          :class="smoothing_window > 1
            ? 'bg-gray-700 text-white border-gray-700'
            : 'bg-white text-gray-500 border-gray-200'"
        >
          Smoothing ({{ smoothing_window > 1 ? smoothing_window : 'Raw' }})
        </PopoverTrigger>
        <PopoverContent align="start" class="w-36 p-2">
          <div class="text-[10px] text-gray-400 uppercase tracking-wide mb-1">rolling average</div>
          <button
            class="block w-full text-left text-xs px-2 py-1 rounded transition-colors"
            :class="smoothing_window === 1 ? 'bg-gray-100 font-medium' : 'hover:bg-gray-50'"
            @click="smoothing_window = 1"
          >
            Raw
          </button>
          <button
            v-for="n in [3, 5]"
            :key="n"
            class="block w-full text-left text-xs px-2 py-1 rounded transition-colors"
            :class="smoothing_window === n ? 'bg-gray-100 font-medium' : 'hover:bg-gray-50'"
            @click="smoothing_window = n"
          >
            {{ n }} games
          </button>
          <div class="flex items-center gap-1 mt-1 px-2 py-1">
            <span class="text-xs text-gray-500">Custom:</span>
            <input
              v-model="custom_input"
              type="number"
              min="1"
              max="100"
              class="w-12 text-xs border rounded px-1 py-0.5"
              placeholder="#"
              @keydown.enter="smoothing_window = Math.max(1, parseInt(custom_input) || 5)"
              @blur="custom_input && (smoothing_window = Math.max(1, parseInt(custom_input) || 5))"
            />
          </div>
        </PopoverContent>
      </Popover>
      <PuzzleTypeSelector @update="on_filter_update" />
    </div>
    <div v-if="loading" class="h-64 flex items-center justify-center text-gray-400 text-sm">
      Loading...
    </div>
    <div v-else-if="visible_types.size === 0" class="h-64 flex items-center justify-center text-gray-400 text-sm">
      No solve data for selected filters
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
      :reference-lines="reference_lines"
    />
  </Container>
</template>
