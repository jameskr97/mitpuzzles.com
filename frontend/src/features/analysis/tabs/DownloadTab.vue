<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import Container from '@/core/components/ui/Container.vue'
import { Badge } from '@/core/components/ui/badge'
import { Button } from '@/core/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/core/components/ui/tabs'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/core/components/ui/table'
import { download_blob } from '@/utils'
import { useAnalysisStore } from '@/features/analysis/stores/useAnalysisStore'
import { api } from '@/core/services/client'

interface ExperimentSummary {
  experiment_id: string
  total_runs: number
  direct_runs: number
  prolific_runs: number
  avg_duration_seconds: number
}

interface FreeplayPreview {
  total: number
  authenticated: number
  anonymous: number
}

const store = useAnalysisStore()
const active_sub_tab = ref('freeplay')

const experiments = ref<ExperimentSummary[]>([])
const loading_experiments = ref(false)

const freeplay_preview = ref<FreeplayPreview | null>(null)
const loading_preview = ref(false)

const format_duration = (seconds: number) => {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}m ${secs.toString().padStart(2, '0')}s`
}

const fetch_experiments = async () => {
  loading_experiments.value = true
  try {
    const { data } = await api.GET('/api/experiment/admin/summary')
    if (data) experiments.value = data as any
  } catch (err) {
    console.error('Failed to fetch experiments:', err)
  } finally {
    loading_experiments.value = false
  }
}

const fetch_freeplay_preview = async () => {
  loading_preview.value = true
  try {
    const query: Record<string, any> = {}
    if (store.puzzle_types.size > 0) query.puzzle_type = [...store.puzzle_types]
    if (store.puzzle_sizes.size > 0) query.puzzle_size = [...store.puzzle_sizes]
    if (store.difficulties.size > 0) query.puzzle_difficulty = [...store.difficulties]
    if (store.selected_entity_id) {
      if (store.scope === 'user') query.filter_user_id = store.selected_entity_id
      else if (store.scope === 'device') query.filter_device_id = store.selected_entity_id
    }
    if (store.solved_filter !== 'all') query.solved_filter = store.solved_filter
    if (store.date_start) query.date_start = store.date_start
    if (store.date_end) query.date_end = store.date_end

    const { data } = await api.GET("/api/puzzle/admin/freeplay/preview", { params: { query } })
    if (data) freeplay_preview.value = data as any
  } catch (err) {
    console.error('Failed to fetch freeplay preview:', err)
  } finally {
    loading_preview.value = false
  }
}

const download_experiment = async (experiment_id: string, platform?: string) => {
  const params = platform ? `?platform=${platform}` : ''
  const url = `/api/experiment/admin/${experiment_id}/export${params}`
  const filename = `${experiment_id}${platform ? `_${platform}` : ''}_export.parquet`
  await download_blob(url, filename)
}

const download_freeplay = async (user_type?: string) => {
  const params = new URLSearchParams()

  if (user_type) {
    params.append('user_type', user_type)
  }

  store.puzzle_types.forEach(type => params.append('puzzle_type', type))
  store.puzzle_sizes.forEach(size => params.append('puzzle_size', size))
  store.difficulties.forEach(diff => params.append('puzzle_difficulty', diff))

  // Add entity filter based on scope
  if (store.selected_entity_id) {
    if (store.scope === 'user') {
      params.append('filter_user_id', store.selected_entity_id)
    } else if (store.scope === 'device') {
      params.append('filter_device_id', store.selected_entity_id)
    }
  }

  if (store.solved_filter !== 'all') {
    params.append('solved_filter', store.solved_filter)
  }
  if (store.date_start) params.append('date_start', store.date_start)
  if (store.date_end) params.append('date_end', store.date_end)

  const query = params.toString() ? `?${params.toString()}` : ''
  const url = `/api/puzzle/admin/freeplay/export${query}`

  const filename_parts = ['freeplay']
  if (store.puzzle_types.size > 0) filename_parts.push([...store.puzzle_types].join('-'))
  if (store.selected_entity_id) filename_parts.push(store.scope)
  if (store.solved_filter !== 'all') filename_parts.push(store.solved_filter)
  if (user_type) filename_parts.push(user_type)
  filename_parts.push('export.parquet')

  await download_blob(url, filename_parts.join('_'))
}

// Watch for filter changes to update preview
watch(
  [() => store.puzzle_types, () => store.puzzle_sizes, () => store.difficulties, () => store.scope, () => store.selected_entity_id, () => store.solved_filter, () => store.date_start, () => store.date_end],
  () => {
    fetch_freeplay_preview()
  },
  { deep: true }
)

onMounted(() => {
  fetch_experiments()
  fetch_freeplay_preview()
})
</script>

<template>
  <div class="h-full overflow-y-auto">
    <div class="flex flex-col gap-2">
      <!-- Sub-tabs: Freeplay / Experiment -->
      <Tabs v-model="active_sub_tab" class="w-full">
        <TabsList class="w-full">
          <TabsTrigger value="freeplay">Freeplay</TabsTrigger>
          <TabsTrigger value="experiment">Experiment</TabsTrigger>
        </TabsList>

        <!-- Freeplay Tab Content -->
        <TabsContent value="freeplay" class="mt-2">
          <Container>
            <!-- Preview counts -->
            <div class="bg-gray-50 rounded-lg p-4 mb-4">
              <div v-if="loading_preview" class="text-sm text-gray-500">Loading...</div>
              <div v-else-if="freeplay_preview" class="grid grid-cols-3 gap-4 text-center">
                <div>
                  <div class="text-2xl font-bold text-blue-600">{{ freeplay_preview.authenticated.toLocaleString() }}</div>
                  <div class="text-xs text-gray-500">Authenticated</div>
                </div>
                <div>
                  <div class="text-2xl font-bold text-green-600">{{ freeplay_preview.anonymous.toLocaleString() }}</div>
                  <div class="text-xs text-gray-500">Anonymous</div>
                </div>
                <div>
                  <div class="text-2xl font-bold text-red-600">{{ freeplay_preview.total.toLocaleString() }}</div>
                  <div class="text-xs text-gray-500">Total</div>
                </div>
              </div>
            </div>

            <div class="flex flex-wrap gap-1">
              <Button
                variant="blue"
                :disabled="!freeplay_preview || freeplay_preview.authenticated === 0"
                @click="download_freeplay('authenticated')"
              >
                Download Authenticated
              </Button>
              <Button
                variant="green"
                :disabled="!freeplay_preview || freeplay_preview.anonymous === 0"
                @click="download_freeplay('anonymous')"
              >
                Download Anonymous
              </Button>
              <Button
                variant="red"
                :disabled="!freeplay_preview || freeplay_preview.total === 0"
                @click="download_freeplay()"
              >
                Download All
              </Button>
            </div>
          </Container>
        </TabsContent>

        <!-- Experiment Tab Content -->
        <TabsContent value="experiment" class="mt-2">
          <Container>
            <div class="text-lg font-semibold mb-3">Experiments</div>
            <div v-if="loading_experiments" class="text-gray-500 text-sm">Loading experiments...</div>
            <Table v-else>
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
                <TableRow v-for="exp in experiments" :key="exp.experiment_id">
                  <TableCell class="font-medium">{{ exp.experiment_id }}</TableCell>
                  <TableCell class="hidden md:table-cell">{{ format_duration(exp.avg_duration_seconds) }}</TableCell>
                  <TableCell>
                    <Badge variant="blue">{{ exp.prolific_runs }}</Badge>
                  </TableCell>
                  <TableCell>
                    <Badge variant="green">{{ exp.direct_runs }}</Badge>
                  </TableCell>
                  <TableCell>
                    <Badge variant="red">{{ exp.total_runs }}</Badge>
                  </TableCell>
                  <TableCell>
                    <div class="flex gap-1">
                      <Button
                        :disabled="exp.prolific_runs === 0"
                        variant="blue"
                        size="sm"
                        @click="download_experiment(exp.experiment_id, 'prolific')"
                      >
                        Prolific
                      </Button>
                      <Button
                        :disabled="exp.direct_runs === 0"
                        variant="green"
                        size="sm"
                        @click="download_experiment(exp.experiment_id, 'direct')"
                      >
                        Direct
                      </Button>
                      <Button
                        :disabled="exp.total_runs === 0"
                        variant="red"
                        size="sm"
                        @click="download_experiment(exp.experiment_id)"
                      >
                        All
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </Container>
        </TabsContent>
      </Tabs>
    </div>
  </div>
</template>
