<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import Container from '@/core/components/ui/Container.vue'
import { Button } from '@/core/components/ui/button'
import PuzzleRenderer from '@/core/components/PuzzleRenderer.vue'
import type { PuzzleDefinition } from '@/core/games/types/puzzle-types.ts'
import JSONContainer from "@/core/components/ui/JSONContainer.vue"
import { api } from '@/core/services/axios'

interface PuzzleStats {
  puzzle_id: string
  total_attempts: number
  solved_attempts: number
  solve_rate: number
  authenticated_attempts: number
  anonymous_attempts: number
  avg_duration_seconds: number | null
  min_duration_seconds: number | null
  max_duration_seconds: number | null
  unique_devices: number
  unique_users: number
}

const props = defineProps<{
  puzzle: PuzzleDefinition | null
  loading?: boolean
}>()

const emit = defineEmits<{
  close: []
}>()

const model = defineModel<boolean>({ default: false })

const stats = ref<PuzzleStats | null>(null)
const loading_stats = ref(false)

const state_solved = computed(() => {
  if (!props.puzzle) return null
  return {
    definition: props.puzzle,
    board: props.puzzle.solution,
  }
})

async function fetch_stats(puzzle_id: string) {
  loading_stats.value = true
  try {
    const response = await api.get(`/api/puzzle/stats/${puzzle_id}`)
    stats.value = response.data
  } catch (error) {
    console.error('Failed to fetch puzzle stats:', error)
    stats.value = null
  } finally {
    loading_stats.value = false
  }
}

// Fetch stats when modal opens or puzzle changes
watch(
  [model, () => props.puzzle?.id],
  ([open, puzzle_id]) => {
    if (open && puzzle_id) {
      fetch_stats(String(puzzle_id))
    } else if (!open) {
      stats.value = null
    }
  },
  { immediate: true }
)

function format_duration(seconds: number | null): string {
  if (seconds === null) return '-'
  if (seconds >= 60) {
    const mins = Math.floor(seconds / 60)
    const secs = (seconds % 60).toFixed(1)
    return `${mins}m ${secs}s`
  }
  return `${seconds.toFixed(1)}s`
}

function close() {
  model.value = false
  emit('close')
}
</script>

<template>
  <Teleport to="body">
    <div
      v-if="model"
      class="fixed inset-0 z-50 flex items-center justify-center p-2 md:p-4 bg-black/50"
      @click="close"
    >
      <div
        class="bg-white rounded-lg shadow-xl w-full max-w-lg max-h-[90vh] flex flex-col"
        @click.stop
      >
        <!-- Header -->
        <div class="flex items-center justify-between p-3 md:p-4 border-b border-gray-200 shrink-0">
          <h3 class="text-base md:text-lg font-semibold text-gray-900">
            Puzzle Definition
            <span v-if="puzzle" class="block md:inline text-sm font-normal text-gray-500 md:ml-2">
              {{ puzzle.puzzle_type }} - {{ puzzle.rows }}x{{ puzzle.cols }}
            </span>
          </h3>
          <button @click="close" class="text-gray-400 hover:text-gray-600 transition-colors p-1">
            <svg class="w-5 h-5 md:w-6 md:h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Body -->
        <div class="grid grid-cols-3 gap-0.5 grid-rows-2 overflow-auto h-82 m-2">
          <!-- Puzzle Solution -->
          <Container class="flex flex-col">
            <div class="text-center font-semibold">Solution</div>
            <div class="flex justify-center mx-auto w-full md:p-3 md:-translate-y-4 translate-x-0.5">
                <PuzzleRenderer
                  v-if="state_solved"
                  :definition="puzzle"
                  :state="state_solved"
                />
                <div v-else class="text-gray-500 text-sm">Solution not available</div>
              </div>
          </Container>

          <JSONContainer :data="puzzle" title="Puzzle Definition" class="col-span-2" />

          <!-- Stats -->
          <Container class="col-span-full p-2">
            <div v-if="loading_stats" class="text-center text-gray-500 text-sm">Loading stats...</div>
            <div v-else-if="stats" class="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
              <div class="text-center">
                <div class="font-semibold text-gray-900">{{ stats.total_attempts }}</div>
                <div class="text-gray-500">Attempts</div>
              </div>
              <div class="text-center">
                <div class="font-semibold text-gray-900">{{ stats.solve_rate }}%</div>
                <div class="text-gray-500">Solve Rate</div>
              </div>
              <div class="text-center">
                <div class="font-semibold text-gray-900">{{ format_duration(stats.avg_duration_seconds) }}</div>
                <div class="text-gray-500">Avg Time</div>
              </div>
              <div class="text-center">
                <div class="font-semibold text-gray-900">{{ format_duration(stats.min_duration_seconds) }}</div>
                <div class="text-gray-500">Best Time</div>
              </div>
            </div>
            <div v-else class="text-center text-gray-400 text-sm">No stats available</div>
          </Container>
        </div>

        <!-- Footer -->
        <div class="flex justify-end p-3 md:p-4 border-t border-gray-200 shrink-0">
          <Button variant="secondary" size="sm" @click="close">Close</Button>
        </div>
      </div>
    </div>
  </Teleport>
</template>
