<script setup lang="ts">
/**
 * GraphConfigurableScatter — admin dashboard widget.
 * Fetches per-attempt metrics via /graphs/attempts and lets the researcher pick x/y axes.
 */
import { ref } from "vue";
import Container from "@/core/components/ui/Container.vue";
import PuzzleTypeSelector from "./PuzzleTypeSelector.vue";
import ConfigurableChart from "./ConfigurableChart.vue";
import type { ChartFeature } from "./ConfigurableChart.vue";
import { api } from "@/core/services/client";

const props = withDefaults(defineProps<{
  defaultX?: string;
  defaultY?: string;
  defaultColor?: string;
}>(), {
  defaultX: "difficulty_score",
  defaultY: "min_actions",
  defaultColor: "puzzle_type",
});

function format_time(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, "0")}`;
}

function format_pct(v: number): string {
  return `${Math.round(v * 100)}%`;
}

const features: ChartFeature[] = [
  { key: "time", label: "Solve Time (s)", type: "number", format: format_time },
  { key: "efficiency", label: "Efficiency", type: "number", format: format_pct },
  { key: "solve_efficiency", label: "Solve Efficiency", type: "number", format: format_pct },
  { key: "mistakes", label: "Mistakes", type: "number" },
  { key: "corrections", label: "Corrections", type: "number" },
  { key: "actual_actions", label: "Total Actions", type: "number" },
  { key: "min_actions", label: "Min Actions", type: "number" },
  { key: "difficulty_score", label: "Puzzle Difficulty", type: "number" },
];

const color_features: ChartFeature[] = [
  { key: "puzzle_type", label: "Puzzle Type", type: "category" },
  { key: "puzzle_size", label: "Puzzle Size", type: "category" },
  { key: "puzzle_difficulty", label: "Difficulty Label", type: "category" },
];

const points = ref<Record<string, any>[]>([]);
const loading = ref(false);
const error = ref<string | null>(null);
const count = ref(0);

async function on_filter_update(filter: { puzzle_type: string; puzzle_size: string; puzzle_difficulty: string }) {
  loading.value = true;
  error.value = null;
  count.value = 0;

  try {
    const params: any = { puzzle_type: filter.puzzle_type };
    if (filter.puzzle_size) params.puzzle_size = filter.puzzle_size;
    if (filter.puzzle_difficulty) params.puzzle_difficulty = filter.puzzle_difficulty;

    const { data, error: fetchError } = await api.GET("/api/puzzle/graphs/attempts" as any, {
      params: { query: params },
    });
    if (fetchError || !data) {
      error.value = "Failed to load data.";
      return;
    }

    points.value = (data as any).attempts ?? [];
    count.value = (data as any).count ?? 0;
  } catch {
    error.value = "Failed to load data.";
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <Container>
    <div class="flex items-start justify-between mb-2">
      <div>
        <span class="text-xs font-semibold text-gray-400 uppercase tracking-wide">Configurable Scatter</span>
        <p v-if="count" class="text-xs text-gray-400">{{ count.toLocaleString() }} solves</p>
      </div>
      <PuzzleTypeSelector @update="on_filter_update" />
    </div>

    <div v-if="loading" class="h-72 flex items-center justify-center text-gray-400 text-sm">Loading...</div>
    <div v-else-if="error" class="h-72 flex items-center justify-center text-red-400 text-sm">{{ error }}</div>
    <div v-else-if="points.length === 0" class="h-72 flex items-center justify-center text-gray-400 text-sm">No solved attempts</div>
    <ConfigurableChart
      v-else
      :points="points"
      :features="features"
      :color-features="color_features"
      :default-x="props.defaultX"
      :default-y="props.defaultY"
      :default-color="props.defaultColor"
      :height="300"
      :point-radius="2"
    />
  </Container>
</template>
