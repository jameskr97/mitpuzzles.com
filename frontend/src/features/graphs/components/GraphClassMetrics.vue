<script setup lang="ts">
/**
 * Aggregate metrics for a puzzle class (type + size + difficulty).
 * Shows average mistakes, efficiency, assists, etc.
 */
import { ref } from "vue";
import Container from "@/core/components/ui/Container.vue";
import { api } from "@/core/services/client";
import PuzzleTypeSelector from "./PuzzleTypeSelector.vue";

const loading = ref(false);
const data = ref<any>(null);

const filter = ref({ puzzle_type: "", puzzle_size: "", puzzle_difficulty: "" });

async function on_filter_update(value: { puzzle_type: string; puzzle_size: string; puzzle_difficulty: string }) {
  filter.value = value;
  loading.value = true;

  const params: any = { puzzle_type: value.puzzle_type };
  if (value.puzzle_size) params.puzzle_size = value.puzzle_size;
  if (value.puzzle_difficulty) params.puzzle_difficulty = value.puzzle_difficulty;

  const { data: result } = await api.GET("/api/puzzle/graphs/class-metrics" as any, {
    params: { query: params },
  });
  data.value = result;
  loading.value = false;
}

function fmt_pct(val: number): string {
  return (val * 100).toFixed(1) + "%";
}
</script>

<template>
  <Container>
    <div class="flex items-start justify-between mb-2">
      <div>
        <div class="text-xs font-semibold text-gray-400 uppercase tracking-wide">Class Metrics</div>
        <p v-if="data?.total" class="text-xs text-gray-400">{{ data.total.toLocaleString() }} solved attempts</p>
      </div>
      <PuzzleTypeSelector puzzle-type="minesweeper" @update="on_filter_update" />
    </div>

    <div v-if="loading" class="text-sm text-gray-400 text-center py-4">Loading...</div>
    <div v-else-if="!data || data.total === 0" class="text-sm text-gray-400 text-center py-4">No data</div>
    <div v-else class="grid grid-cols-3 gap-3">
      <div class="flex flex-col items-center p-2 rounded bg-gray-50">
        <span class="text-2xl font-bold">{{ fmt_pct(data.avg_efficiency) }}</span>
        <span class="text-xs text-gray-500">Avg Efficiency</span>
      </div>
      <div class="flex flex-col items-center p-2 rounded bg-gray-50">
        <span class="text-2xl font-bold">{{ fmt_pct(data.avg_solve_efficiency) }}</span>
        <span class="text-xs text-gray-500">Avg Solve Efficiency</span>
      </div>
      <div class="flex flex-col items-center p-2 rounded bg-gray-50">
        <span class="text-2xl font-bold">{{ fmt_pct(data.perfect_rate / 100) }}</span>
        <span class="text-xs text-gray-500">Perfect Games</span>
      </div>
      <div class="flex flex-col items-center p-2 rounded bg-gray-50">
        <span class="text-2xl font-bold">{{ data.avg_mistakes }}</span>
        <span class="text-xs text-gray-500">Avg Mistakes</span>
      </div>
      <div class="flex flex-col items-center p-2 rounded bg-gray-50">
        <span class="text-2xl font-bold">{{ data.avg_corrections }}</span>
        <span class="text-xs text-gray-500">Avg Corrections</span>
      </div>
      <div class="flex flex-col items-center p-2 rounded bg-gray-50">
        <span class="text-2xl font-bold">{{ data.avg_assists }}</span>
        <span class="text-xs text-gray-500">Avg Assists</span>
      </div>
      <div class="flex flex-col items-center p-2 rounded bg-gray-50">
        <span class="text-2xl font-bold">{{ data.avg_actual_actions }}</span>
        <span class="text-xs text-gray-500">Avg Actions</span>
      </div>
      <div class="flex flex-col items-center p-2 rounded bg-gray-50">
        <span class="text-2xl font-bold">{{ data.avg_min_actions }}</span>
        <span class="text-xs text-gray-500">Avg Min Actions</span>
      </div>
      <div class="flex flex-col items-center p-2 rounded bg-gray-50">
        <span class="text-2xl font-bold">{{ data.perfect_count }}</span>
        <span class="text-xs text-gray-500">Perfect Count</span>
      </div>
    </div>
  </Container>
</template>
