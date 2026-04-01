<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";
import { useAsyncState } from "@vueuse/core";
import Container from "@/core/components/ui/Container.vue";
import { ACTIVE_GAMES } from "@/constants";
import PuzzleLeaderboard from "@/core/components/PuzzleLeaderboard.vue";
import GraphClickOrderHeatmap from "@/features/graphs/components/GraphClickOrderHeatmap.vue";

const route = useRoute();
const puzzle_id = route.params.puzzle_id as string;

const { state: data, isLoading: loading, error } = useAsyncState(
  async () => {
    const res = await fetch(`/api/puzzle/admin/puzzle/${puzzle_id}`, { credentials: "include" });
    if (!res.ok) throw new Error(res.status === 404 ? "Puzzle not found" : "Failed to load");
    return await res.json();
  },
  null,
);

const puzzle = computed(() => data.value?.puzzle);
const stats = computed(() => data.value?.stats);
const metrics = computed(() => data.value?.metrics);
const attempts = computed(() => data.value?.attempts ?? []);
const canvas_component = computed(() => (puzzle.value ? ACTIVE_GAMES[puzzle.value.puzzle_type]?.component : null));

function capitalize(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

function format_time(seconds: number | null): string {
  if (seconds === null) return "-";
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, "0")}`;
}
</script>

<template>
  <div v-if="loading" class="flex justify-center py-20">
    <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900" />
  </div>

  <div v-else-if="error" class="text-center py-20 text-gray-500">{{ error.message }}</div>

  <div v-else-if="puzzle" class="grid grid-cols-2 md:grid-cols-4 gap-2">
    <!-- header -->
    <Container class="col-span-2 md:col-span-4">
      <h1 class="text-xl font-bold">
        {{ capitalize(puzzle.puzzle_type) }} · {{ puzzle.puzzle_size }} {{ puzzle.puzzle_difficulty ?? "" }}
      </h1>
      <p class="text-xs text-gray-400">{{ puzzle_id }}</p>
    </Container>

    <!-- solution -->
    <Container>
      <div class="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">Solution</div>
      <div class="aspect-square pointer-events-none select-none">
        <component
          v-if="canvas_component && puzzle.solution"
          :is="canvas_component"
          :state="{ definition: puzzle, board: puzzle.solution }"
        />
      </div>
    </Container>

    <!-- stats -->
    <Container>
      <div class="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">Stats</div>
      <div class="flex flex-col gap-0.5 text-sm">
        <div class="flex justify-between">
          <span class="text-gray-500">Attempts</span>
          <span class="font-medium tabular-nums">{{ stats.total_attempts }}</span>
        </div>
        <div class="flex justify-between">
          <span class="text-gray-500">Solved</span>
          <span class="font-medium tabular-nums">{{ stats.solved }}</span>
        </div>
        <div class="flex justify-between">
          <span class="text-gray-500">Solve Rate</span>
          <span class="font-medium tabular-nums">{{ stats.solve_rate }}%</span>
        </div>
        <div class="flex justify-between">
          <span class="text-gray-500">Best Time</span>
          <span class="font-medium tabular-nums">{{ format_time(stats.best_time) }}</span>
        </div>
        <div class="flex justify-between">
          <span class="text-gray-500">Avg Time</span>
          <span class="font-medium tabular-nums">{{ format_time(stats.avg_time) }}</span>
        </div>
        <template v-if="metrics">
          <hr class="my-1" />
          <div class="flex justify-between">
            <span class="text-gray-500">Min Actions</span>
            <span class="font-medium tabular-nums">{{ metrics.min_actions }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-gray-500">Board Size</span>
            <span class="font-medium tabular-nums">{{ metrics.board_size }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-gray-500">Solution Density</span>
            <span class="font-medium tabular-nums">{{ (metrics.solution_density * 100).toFixed(1) }}%</span>
          </div>
        </template>
      </div>
    </Container>

    <!-- leaderboard -->
    <PuzzleLeaderboard :puzzle_id="puzzle_id" />

    <!-- recent attempts -->
    <Container class="aspect-square overflow-y-scroll">
      <div class="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">Recent Attempts</div>
      <div class="flex flex-col">
        <router-link
          v-for="a in attempts"
          :key="a.attempt_id"
          :to="{ name: 'game-playback', params: { attempt_id: a.attempt_id } }"
          class="flex items-center justify-between py-1 px-1 border-b border-gray-100 last:border-0 hover:bg-gray-50 rounded text-sm"
        >
          <span>{{ a.username ?? "Anonymous" }}</span>
          <div class="flex items-center gap-3">
            <span
              v-if="a.metrics?.efficiency != null"
              class="text-xs tabular-nums"
              :class="
                a.metrics.efficiency >= 0.8
                  ? 'text-green-500'
                  : a.metrics.efficiency >= 0.5
                    ? 'text-amber-500'
                    : 'text-red-400'
              "
            >
              {{ Math.round(a.metrics.efficiency * 100) }}%
            </span>
            <span class="font-semibold tabular-nums" :class="a.is_solved ? 'text-green-600' : 'text-red-400'">
              {{ a.is_solved ? format_time(a.time) : "DNF" }}
            </span>
          </div>
        </router-link>
      </div>
    </Container>

    <!-- graphs -->
    <GraphClickOrderHeatmap :puzzle-id="puzzle_id" class="col-span-2" />
  </div>
</template>
