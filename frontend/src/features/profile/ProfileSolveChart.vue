<script setup lang="ts">
import { ref, computed } from "vue";
import { Line } from "vue-chartjs";
import {
  Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement,
  TimeScale, Title, Tooltip, Legend, Filler,
} from "chart.js";
import zoomPlugin from "chartjs-plugin-zoom";
import Container from "@/core/components/ui/Container.vue";
import { ACTIVE_GAMES } from "@/constants";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, TimeScale, Title, Tooltip, Legend, Filler, zoomPlugin);

const CHART_COLORS: Record<string, string> = {
  sudoku: "#3b82f6", nonograms: "#ef4444", minesweeper: "#22c55e",
  lightup: "#f59e0b", hashi: "#8b5cf6", mosaic: "#ec4899",
  tents: "#14b8a6", aquarium: "#06b6d4", kakurasu: "#f97316",
};

const props = defineProps<{
  solve_time_history: Record<string, { date: string; avg_time: number }[]>;
}>();

const visible_types = ref<Set<string>>(new Set(Object.keys(props.solve_time_history)));

const time_range = ref<string>("ALL");
const TIME_RANGES: { label: string; value: string; days: number | null }[] = [
  { label: "1M", value: "1M", days: 30 },
  { label: "3M", value: "3M", days: 90 },
  { label: "6M", value: "6M", days: 180 },
  { label: "1Y", value: "1Y", days: 365 },
  { label: "ALL", value: "ALL", days: null },
];

function toggle_type(puzzle_type: string) {
  if (visible_types.value.has(puzzle_type)) {
    visible_types.value.delete(puzzle_type);
  } else {
    visible_types.value.add(puzzle_type);
  }
  visible_types.value = new Set(visible_types.value);
}

function filtered_history(type: string): { date: string; avg_time: number }[] {
  const points = (props.solve_time_history[type] ?? []).filter(p => p.avg_time <= 600);
  const range = TIME_RANGES.find(r => r.value === time_range.value);
  if (!range?.days) return points;
  const cutoff = new Date();
  cutoff.setDate(cutoff.getDate() - range.days);
  const cutoff_str = cutoff.toISOString().slice(0, 10);
  return points.filter(p => p.date >= cutoff_str);
}

const chart_labels = computed(() => {
  const dates = new Set<string>();
  for (const type of visible_types.value) {
    for (const point of filtered_history(type)) {
      dates.add(point.date);
    }
  }
  return [...dates].sort();
});

function capitalize(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

function format_time(seconds: number | null): string {
  if (seconds === null) return "-";
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, "0")}`;
}

function get_game_icon(puzzle_type: string): string {
  return ACTIVE_GAMES[puzzle_type]?.icon ?? "🧩";
}

const chart_data = computed(() => ({
  labels: chart_labels.value.map(d => {
    const date = new Date(d + "T00:00:00");
    return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  }),
  datasets: [...visible_types.value].map(type => {
    const points = filtered_history(type);
    const date_map = new Map(points.map(p => [p.date, p.avg_time]));
    let last: number | null = null;
    const data = chart_labels.value.map(d => {
      const val = date_map.get(d);
      if (val != null) last = val;
      return last;
    });
    return {
      label: capitalize(type),
      data,
      borderColor: CHART_COLORS[type] ?? "#888",
      backgroundColor: (CHART_COLORS[type] ?? "#888") + "18",
      stepped: "before" as const,
      spanGaps: true,
      pointRadius: 3,
      pointHoverRadius: 5,
      borderWidth: 2,
      fill: false,
    };
  }),
}));

const chart_options = {
  responsive: true,
  maintainAspectRatio: false,
  interaction: { mode: "index" as const, intersect: false },
  scales: {
    y: {
      reverse: false,
      title: { display: true, text: "avg solve time (s)" },
      ticks: {
        callback: (value: number | string) => format_time(Number(value)),
      },
    },
    x: { title: { display: false } },
  },
  plugins: {
    legend: { display: false },
    tooltip: {
      mode: "index" as const,
      intersect: false,
      usePointStyle: true,
      callbacks: {
        title: (items: any[]) => {
          if (!items.length) return "";
          const idx = items[0].dataIndex;
          const date_str = chart_labels.value[idx];
          if (!date_str) return "";
          const d = new Date(date_str + "T00:00:00");
          return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
        },
        label: (ctx: any) => {
          if (ctx.parsed.y == null) return "";
          return ` ${ctx.dataset.label}: ${format_time(ctx.parsed.y)}`;
        },
      },
      filter: (item: any) => item.parsed.y != null,
    },
    zoom: {
      pan: { enabled: true, mode: "x" as const },
      zoom: {
        wheel: { enabled: true },
        pinch: { enabled: true },
        mode: "x" as const,
      },
    },
  },
};
</script>

<template>
  <Container>
    <div class="flex items-center gap-1 mb-2">
      <button
        v-for="range in TIME_RANGES"
        :key="range.value"
        class="px-2.5 py-1 text-xs font-medium rounded border transition-colors"
        :class="time_range === range.value
          ? 'bg-blue-600 text-white border-blue-600'
          : 'bg-white text-gray-600 border-gray-300 hover:border-gray-400'"
        @click="time_range = range.value"
      >
        {{ range.label }}
      </button>
      <div class="flex items-center gap-1 ml-auto">
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
    </div>
    <div class="h-64">
      <Line :data="chart_data" :options="chart_options" />
    </div>
  </Container>
</template>
