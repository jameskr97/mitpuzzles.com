<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";
import Container from "@/core/components/ui/Container.vue";
import PlaybackTimeline from "@/features/playback/components/PlaybackTimeline.vue";
import { usePlayback } from "@/features/playback/composables/usePlayback";
import PuzzleLeaderboard from "@/core/components/PuzzleLeaderboard.vue";

const route = useRoute();
const attempt_id = route.params.attempt_id as string;

const {
  loading,
  error,
  puzzle_type,
  canvas_component,
  canvas_state,
  frames,
  is_solved,
  metrics,
  username,
  controls,
  clamped_frame,
  puzzle_definition,
  timestamp_start,
  timestamp_finish,
} = usePlayback(attempt_id);

const solve_date = computed(() => {
  if (!timestamp_start.value) return null;
  const d = new Date(timestamp_start.value);
  return (
    d.toLocaleDateString("en-US", { day: "numeric", month: "long", year: "numeric" }) +
    ", " +
    d.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" })
  );
});

function capitalize(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

const duration = computed(() => {
  if (!timestamp_start.value || !timestamp_finish.value) return null;
  return (timestamp_finish.value - timestamp_start.value) / 1000;
});

function format_time(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, "0")}`;
}

function format_pct(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

const metrics_rows = computed(() => {
  const m = metrics.value;
  if (!m) return [];
  const rows: { label: string; value: string; desc: string }[] = [];

  if (duration.value != null)
    rows.push({
      label: "Time",
      value: format_time(duration.value),
      desc: "Total time from first seeing the puzzle to submitting the solution.",
    });
  if (m.efficiency != null)
    rows.push({
      label: "Efficiency",
      value: format_pct(m.efficiency),
      desc: "Min actions / total actions. Penalizes assist marks (flags, crosses). 100% = no wasted clicks.",
    });
  if (m.solve_efficiency != null)
    rows.push({
      label: "Solve Efficiency",
      value: format_pct(m.solve_efficiency),
      desc: "Min actions / (total actions - assists). Ignores assist marks, only counts placements and mistakes.",
    });
  if (m.min_actions != null)
    rows.push({
      label: "Min Actions",
      value: String(m.min_actions),
      desc: "Minimum number of clicks needed to solve this puzzle. One click per required cell.",
    });
  if (m.actual_actions != null)
    rows.push({
      label: "Actual Actions",
      value: String(m.actual_actions),
      desc: "Total cell-change actions the player made, including assists and mistakes.",
    });
  if (m.positive_actions != null)
    rows.push({
      label: "Positive",
      value: String(m.positive_actions),
      desc: "Actions that placed a required value (correct or incorrect placement attempts).",
    });
  if (m.assist_actions != null)
    rows.push({
      label: "Assists",
      value: String(m.assist_actions),
      desc: "Actions that placed helper marks (flags, crosses, safe marks). Not required to solve.",
    });
  if (m.mistakes != null)
    rows.push({
      label: "Mistakes",
      value: String(m.mistakes),
      desc: "Actions where the player placed a wrong value in a cell.",
    });
  if (m.corrections != null)
    rows.push({
      label: "Corrections",
      value: String(m.corrections),
      desc: "Actions where the player fixed a previously incorrect cell to the correct value.",
    });

  return rows;
});
</script>

<template>
  <div class="grid grid-cols-4 gap-2">
    <!-- board + timeline -->
    <Container class="flex justify-between gap-2 col-span-2 row-span-2 max-h-fit">
      <div class="w-full aspect-square mx-auto pointer-events-none select-none">
        <component v-if="canvas_component && canvas_state" :is="canvas_component" :state="canvas_state" />
      </div>
    </Container>

    <!-- player info -->
    <Container>
      <div class="flex flex-col gap-1">
        <router-link
          v-if="username"
          :to="{ name: 'user-profile', params: { username } }"
          class="text-2xl font-bold text-blue-600 hover:underline"
        >
          {{ username }}
        </router-link>
        <span v-else class="text-sm text-gray-400">Anonymous</span>
        <span v-if="solve_date" class="text-xs text-gray-400">{{ solve_date }}</span>
      </div>
      <hr class="my-2" />
      <div class="flex flex-col gap-0.5 text-sm">
        <div v-if="duration">
          Time: <strong class="tabular-nums">{{ duration.toFixed(3) }} sec</strong>
        </div>
        <div v-if="metrics?.min_actions != null">
          Min Actions: <strong class="tabular-nums">{{ metrics.min_actions }}</strong>
        </div>
        <div v-if="duration && metrics?.actual_actions">
          Speed: <strong class="tabular-nums">{{ (metrics.actual_actions / duration).toFixed(2) }} actions/s</strong>
        </div>
        <div v-if="metrics?.actual_actions != null">
          Actions: <strong class="tabular-nums">{{ metrics.actual_actions }}</strong>
        </div>
        <div v-if="metrics?.efficiency != null">
          Efficiency: <strong class="tabular-nums">{{ format_pct(metrics.efficiency) }}</strong>
        </div>
      </div>
    </Container>

    <!-- metrics -->
    <Container>
      <div class="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">
        {{ capitalize(puzzle_type) }} · {{ puzzle_definition?.puzzle_size }}
        {{ puzzle_definition?.puzzle_difficulty ?? "" }}
      </div>
      <div v-if="metrics_rows.length > 0" class="flex flex-col">
        <div
          v-for="row in metrics_rows"
          :key="row.label"
          class="flex items-center justify-between py-0.5 text-sm"
          :title="row.desc"
        >
          <span class="text-gray-500 underline decoration-dotted decoration-gray-400 underline-offset-2 cursor-help">{{
            row.label
          }}</span>
          <span class="font-medium tabular-nums">{{ row.value }}</span>
        </div>
      </div>
      <div v-else class="text-sm text-gray-400 py-2">No metrics available</div>
    </Container>

    <!-- placeholders for future content -->
    <PuzzleLeaderboard v-if="puzzle_definition" :puzzle_id="puzzle_definition.id" class="row-span-2" />

    <div class="border-gray-200 border rounded w-full row-span-2">{{ puzzle_definition.id }}</div>

    <Container class="col-span-2">
      <PlaybackTimeline
        :frames="frames"
        :current_frame="clamped_frame"
        :is_playing="controls.is_playing.value"
        :moves_per_second="controls.moves_per_second.value"
        @seek="controls.seek"
        @toggle-play="controls.toggle_play"
        @set-mps="controls.set_mps"
      />
    </Container>

    <Container class="col-span-4 text-2xl text-center">
      Statistics & Graphs
    </Container>

    <div class="border-gray-200 border rounded w-full aspect-square"></div>
    <div class="border-gray-200 border rounded w-full aspect-square"></div>
    <div class="border-gray-200 border rounded w-full aspect-square"></div>
    <div class="border-gray-200 border rounded w-full aspect-square"></div>
    <div class="border-gray-200 border rounded w-full aspect-square"></div>
    <div class="border-gray-200 border rounded w-full aspect-square"></div>
  </div>
</template>
