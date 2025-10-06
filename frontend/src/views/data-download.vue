<script setup lang="ts">
import { onMounted, ref } from "vue";
import axios from "axios";
import Container from "@/components/ui/Container.vue";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { download_blob } from "@/utils.ts";

interface experiment_summary {
  experiment_id: string;
  total_runs: number;
  direct_runs: number;
  prolific_runs: number;
  avg_duration_seconds: number;
}

interface experiment_details extends experiment_summary {
  node_stats: {
    node_name: string;
    avg_time_seconds: number;
  }[];
}

interface game_summary {
  puzzle_type: string;
  total_puzzles: number;
  total_attempts: number;
  authenticated_attempts: number;
  anonymous_attempts: number;
  solved_attempts: number;
}

const experiments = ref<experiment_summary[]>([]);
const experiment_details_cache = ref<Map<string, experiment_details>>(new Map());
const expanded_experiments = ref<Set<string>>(new Set());

const games = ref<game_summary[]>([]);
const expanded_games = ref<Set<string>>(new Set());

const loading = ref(false);
const games_loading = ref(false);
const error = ref<string | null>(null);
const games_error = ref<string | null>(null);

// api functions
const fetch_experiments_summary = async () => {
  try {
    loading.value = true;
    error.value = null;
    const response = await axios.get("/api/experiment/admin/summary");
    experiments.value = response.data;
  } catch (err) {
    error.value = "failed to load experiments summary";
    console.error("error fetching experiments summary:", err);
  } finally {
    loading.value = false;
  }
};

const format_duration = (seconds: number) => {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}m ${secs.toString().padStart(2, "0")}s`;
};

const download_experiment = async (experiment_id: string, platform?: string) => {
  const params = platform ? `?platform=${platform}` : "";
  const url = `/api/experiment/admin/${experiment_id}/export${params}`;
  const filename = `${experiment_id}${platform ? `_${platform}` : ""}_export.json`;
  await download_blob(url, filename);
};

const download_game = async (puzzle_type: string, user_type?: string) => {
  const params = user_type ? `?user_type=${user_type}` : "";
  const url = `/api/puzzle/admin/${puzzle_type}/export${params}`;
  const filename = `${puzzle_type}${user_type ? `_${user_type}` : ""}_export.json`;
  await download_blob(url, filename);
};

// api functions for games
const fetch_games_summary = async () => {
  try {
    games_loading.value = true;
    games_error.value = null;
    const response = await axios.get("/api/puzzle/admin/summary");
    games.value = response.data.sort((a: game_summary, b: game_summary) => b.total_attempts - a.total_attempts);
  } catch (err) {
    games_error.value = "failed to load games summary";
    console.error("error fetching games summary:", err);
  } finally {
    games_loading.value = false;
  }
};

// load data on mount
onMounted(() => {
  fetch_experiments_summary();
  fetch_games_summary();
});
</script>

<template>
  <div class="flex flex-col gap-2 mt-2 mx-2 md:mr-2">
    <Container class="max-w-fit">
      <div class="w-full">
        <div class="text-2xl font-semibold mb-4">Experiments</div>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Experiment ID</TableHead>
              <TableHead class="hidden md:table-cell">Avg Duration</TableHead>
              <TableHead>Prolific</TableHead>
              <TableHead>Direct</TableHead>
              <TableHead>Total</TableHead>
              <TableHead>Download</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow v-for="experiment in experiments" :key="experiment.experiment_id">
              <TableCell class="font-medium">{{ experiment.experiment_id }}</TableCell>
              <TableCell class="hidden md:table-cell">{{ format_duration(experiment.avg_duration_seconds) }}</TableCell>
              <TableCell>
                <Badge variant="blue">{{ experiment.prolific_runs }}</Badge>
              </TableCell>
              <TableCell>
                <Badge variant="green">{{ experiment.direct_runs }}</Badge>
              </TableCell>
              <TableCell>
                <Badge variant="red">{{ experiment.total_runs }}</Badge>
              </TableCell>
              <TableCell>
                <div class="flex gap-1">
                  <Button
                    :disabled="experiment.prolific_runs === 0"
                    variant="blue"
                    size="sm"
                    @click="download_experiment(experiment.experiment_id, 'prolific')"
                    >Prolific</Button
                  >
                  <Button
                    :disabled="experiment.direct_runs === 0"
                    variant="green"
                    size="sm"
                    @click="download_experiment(experiment.experiment_id, 'direct')"
                    >Direct</Button
                  >
                  <Button
                    :disabled="experiment.direct_runs === 0 && experiment.prolific_runs === 0"
                    variant="red"
                    size="sm"
                    @click="download_experiment(experiment.experiment_id)"
                    >All</Button
                  >
                </div>
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </div>
    </Container>
    <Container class="max-w-fit">
      <div class="w-full">
        <div class="text-2xl font-semibold mb-4">Games</div>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Game Type</TableHead>
              <TableHead>User</TableHead>
              <TableHead>Anon</TableHead>
              <TableHead>Download</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow
              v-for="game in games"
              :key="game.puzzle_type"
              :class="{ 'opacity-50': game.authenticated_attempts === 0 && game.anonymous_attempts === 0 }"
            >
              <TableCell class="font-medium">
                <Badge variant="red">{{ game.total_attempts }}</Badge>
                {{ game.puzzle_type.at(0)?.toUpperCase() + game.puzzle_type.slice(1) }}

              </TableCell>
              <TableCell>
                <Badge variant="blue">{{ game.authenticated_attempts }}</Badge>
              </TableCell>
              <TableCell>
                <Badge variant="green">{{ game.anonymous_attempts }}</Badge>
              </TableCell>
              <TableCell>
                <div class="flex gap-1">
                  <Button
                    :disabled="game.authenticated_attempts === 0"
                    variant="blue"
                    size="sm"
                    @click="download_game(game.puzzle_type, 'authenticated')"
                    >Authenticated</Button
                  >
                  <Button
                    :disabled="game.anonymous_attempts === 0"
                    variant="green"
                    size="sm"
                    @click="download_game(game.puzzle_type, 'anonymous')"
                    >Anonymous</Button
                  >
                  <Button
                    :disabled="game.authenticated_attempts === 0 && game.anonymous_attempts === 0"
                    variant="red"
                    size="sm"
                    @click="download_game(game.puzzle_type)"
                    >All</Button
                  >
                </div>
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </div>
    </Container>
  </div>
</template>
