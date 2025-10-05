<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import Container from '@/components/ui/Container.vue'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Table, TableHeader, TableBody, TableHead, TableRow, TableCell } from '@/components/ui/table'
import { Separator } from '@/components/ui/separator'
import { download_blob } from "@/utils.ts";

interface experiment_summary {
  experiment_id: string
  total_runs: number
  direct_runs: number
  prolific_runs: number
  avg_duration_seconds: number
}

interface experiment_details extends experiment_summary {
  node_stats: {
    node_name: string
    avg_time_seconds: number
  }[]
}

interface game_summary {
  puzzle_type: string
  total_puzzles: number
  total_attempts: number
  authenticated_attempts: number
  anonymous_attempts: number
  solved_attempts: number
}

const experiments = ref<experiment_summary[]>([])
const experiment_details_cache = ref<Map<string, experiment_details>>(new Map())
const expanded_experiments = ref<Set<string>>(new Set())

const games = ref<game_summary[]>([])
const expanded_games = ref<Set<string>>(new Set())

const loading = ref(false)
const games_loading = ref(false)
const error = ref<string | null>(null)
const games_error = ref<string | null>(null)

// api functions
const fetch_experiments_summary = async () => {
  try {
    loading.value = true
    error.value = null
    const response = await axios.get('/api/experiment/admin/summary')
    experiments.value = response.data
  } catch (err) {
    error.value = 'failed to load experiments summary'
    console.error('error fetching experiments summary:', err)
  } finally {
    loading.value = false
  }
}

const format_duration = (seconds: number) => {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}m ${secs.toString().padStart(2, '0')}s`
}

const download_experiment = async (experiment_id: string, platform?: string) => {
  const params = platform ? `?platform=${platform}` : ''
  const url = `/api/experiment/admin/${experiment_id}/export${params}`
  const filename = `${experiment_id}${platform ? `_${platform}` : ''}_export.json`
  await download_blob(url, filename)
}

const download_game = async (puzzle_type: string, user_type?: string) => {
  const params = user_type ? `?user_type=${user_type}` : ''
  const url = `/api/puzzle/admin/${puzzle_type}/export${params}`
  const filename = `${puzzle_type}${user_type ? `_${user_type}` : ''}_export.json`
  await download_blob(url, filename)
}

// api functions for games
const fetch_games_summary = async () => {
  try {
    games_loading.value = true
    games_error.value = null
    const response = await axios.get('/api/puzzle/admin/summary')
    games.value = response.data.sort((a: game_summary, b: game_summary) => b.total_attempts - a.total_attempts)
  } catch (err) {
    games_error.value = 'failed to load games summary'
    console.error('error fetching games summary:', err)
  } finally {
    games_loading.value = false
  }
}

// load data on mount
onMounted(() => {
  fetch_experiments_summary()
  fetch_games_summary()
})
</script>

<template>
    <Container class="flex flex-col mt-2 mr-2 xl:max-w-130 gap-2 h-[calc(100vh-1rem)] overflow-y-scroll bg-slate-300!">
      <!-- experiments -->
      <Card v-for="experiment in experiments" class="w-full">
        <CardContent>
            <div class="text-xl">
              <span class="font-bold">Experiment: </span>
              <span class="">{{ experiment.experiment_id }}</span>
            </div>
            <div class="flex flex-row flex-wrap gap-1 mt-2">
              <Badge class="hidden md:block" variant="outline">avg duration: {{ format_duration(experiment.avg_duration_seconds) }}</Badge>
              <Badge variant="blue">{{ experiment.prolific_runs }} prolific</Badge>
              <Badge variant="green">{{ experiment.direct_runs }} direct</Badge>
              <Badge variant="red">{{ experiment.total_runs }} total runs</Badge>
            </div>
          <div class="flex flex-wrap mt-2 gap-1">
            <Button :disabled="experiment.prolific_runs === 0" variant="blue" size="sm" @click="download_experiment(experiment.experiment_id, 'prolific')">Download Prolific</Button>
            <Button :disabled="experiment.direct_runs === 0" variant="green" size="sm" @click="download_experiment(experiment.experiment_id, 'direct')">Download Direct</Button>
            <Button :disabled="experiment.direct_runs === 0 && experiment.prolific_runs === 0" variant="red" size="sm" @click="download_experiment(experiment.experiment_id)">Download All</Button>
          </div>
        </CardContent>
      </Card>

      <!-- game data -->
      <Card v-for="game in games" class="w-full xl:max-w-130" :class="{ 'opacity-50': game.authenticated_attempts === 0 && game.anonymous_attempts === 0 }">
        <CardContent>
            <div class="text-xl">
              <span class="font-bold">Game: </span>
              <span class="">{{ game.puzzle_type }}</span>
            </div>
            <div class="flex flex-wrap gap-3 mt-2">
              <Badge variant="outline">avg duration: {{  }}</Badge>
              <Badge variant="blue">{{ game.authenticated_attempts }} user games</Badge>
              <Badge variant="green">{{ game.anonymous_attempts }} anonymous plays</Badge>
              <Badge variant="red">{{ game.total_attempts }} total plays</Badge>
            </div>
          <div class="flex mt-2 flex-wrap gap-3">
            <Button :disabled="game.authenticated_attempts === 0" variant="blue" size="sm" @click="download_game(game.puzzle_type, 'authenticated')">Download Authenticated</Button>
            <Button :disabled="game.anonymous_attempts === 0" variant="green" size="sm" @click="download_game(game.puzzle_type, 'anonymous')">Download Anonymous</Button>
            <Button :disabled="game.authenticated_attempts === 0 && game.anonymous_attempts === 0" variant="red" size="sm" @click="download_game(game.puzzle_type)">Download All</Button>
          </div>
        </CardContent>
      </Card>

    </Container>
</template>

