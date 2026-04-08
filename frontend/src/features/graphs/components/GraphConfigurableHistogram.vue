<script setup lang="ts">
/**
 * GraphConfigurableHistogram — admin dashboard widget.
 * Fetches per-attempt metrics via /graphs/attempts and lets the researcher pick which feature to histogram.
 */
import { ref } from "vue";
import Container from "@/core/components/ui/Container.vue";
import PuzzleTypeSelector from "./PuzzleTypeSelector.vue";
import ConfigurableHistogram from "./ConfigurableHistogram.vue";
import type { ChartFeature } from "./ConfigurableChart.vue";
import { api } from "@/core/services/client";

const props = withDefaults(defineProps<{
  defaultFeature?: string;
}>(), {
  defaultFeature: "time",
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
  { key: "assist_actions", label: "Assist Actions", type: "number" },
  { key: "wasted_actions", label: "Wasted Actions", type: "number" },
  { key: "difficulty_score", label: "Puzzle Difficulty", type: "number" },
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
        <span class="text-xs font-semibold text-gray-400 uppercase tracking-wide">Configurable Distribution</span>
        <p v-if="count" class="text-xs text-gray-400">{{ count.toLocaleString() }} solves (95th percentile cutoff)</p>
      </div>
      <PuzzleTypeSelector @update="on_filter_update" />
    </div>

    <div v-if="loading" class="h-64 flex items-center justify-center text-gray-400 text-sm">Loading...</div>
    <div v-else-if="error" class="h-64 flex items-center justify-center text-red-400 text-sm">{{ error }}</div>
    <div v-else-if="points.length === 0" class="h-64 flex items-center justify-center text-gray-400 text-sm">No solved attempts</div>
    <ConfigurableHistogram
      v-else
      :points="points"
      :features="features"
      :default-feature="props.defaultFeature"
      :height="256"
    />
  </Container>
</template>
