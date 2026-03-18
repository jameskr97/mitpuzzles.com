<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useAnalysisStore } from '@/features/analysis/stores/useAnalysisStore'
import { api } from '@/core/services/client'
import Container from '@/core/components/ui/Container.vue'
import PuzzleBrowserItem from '@/features/analysis/components/PuzzleBrowserItem.vue'
import PuzzleDefinitionModal from '@/features/analysis/components/PuzzleDefinitionModal.vue'
import type { PuzzleDefinition } from '@/core/games/types/puzzle-types.ts'

const store = useAnalysisStore()

// Local state for puzzle browsing
const all_puzzles = ref<any[]>([])
const total_count = ref(0)
const current_offset = ref(0)
const has_more = ref(true)
const loading_puzzles = ref(false)
const grid_size = ref<'small' | 'medium' | 'large'>('medium')

// Infinite scroll
const scroll_sentinel = ref<HTMLElement | null>(null)
let intersection_observer: IntersectionObserver | null = null

// Modal state
const show_definition_modal = ref(false)
const selected_puzzle_definition = ref<PuzzleDefinition | null>(null)
const loading_definition = ref(false)

// Grid configuration
const grid_config = computed(() => {
  switch (grid_size.value) {
    case 'small':
      return { cols: 'grid-cols-4 md:grid-cols-6 lg:grid-cols-8', puzzles_per_page: 48 }
    case 'medium':
      return { cols: 'grid-cols-3 md:grid-cols-4 lg:grid-cols-6', puzzles_per_page: 24 }
    case 'large':
      return { cols: 'grid-cols-2 md:grid-cols-3 lg:grid-cols-4', puzzles_per_page: 16 }
    default:
      return { cols: 'grid-cols-3 md:grid-cols-4 lg:grid-cols-6', puzzles_per_page: 24 }
  }
})

const displayed_puzzles = computed(() => all_puzzles.value)
const show_load_more = computed(() => has_more.value && !loading_puzzles.value)

// Fetch puzzles
async function fetch_puzzles(append: boolean = false) {
  loading_puzzles.value = true

  try {
    const params: Record<string, string | string[]> = {
      limit: grid_config.value.puzzles_per_page.toString(),
      offset: current_offset.value.toString(),
      include_solution: 'true',
    }

    // Add filters from store
    if (store.puzzle_id) {
      params.puzzle_id = store.puzzle_id
    }
    if (store.puzzle_types.size > 0) {
      params.puzzle_type = [...store.puzzle_types]
    }
    if (store.puzzle_sizes.size > 0) {
      params.puzzle_size = [...store.puzzle_sizes]
    }
    if (store.difficulties.size > 0) {
      params.puzzle_difficulty = [...store.difficulties]
    }
    if (store.has_attempts !== 'all') {
      params.has_attempts = store.has_attempts
    }

    const { data, error } = await api.GET('/api/puzzle/browse', {
      params: { query: params as any },
    })
    if (error) return

    if (append) {
      all_puzzles.value = [...all_puzzles.value, ...data.puzzles]
    } else {
      all_puzzles.value = data.puzzles
    }

    total_count.value = data.total_count
    has_more.value = data.has_more
    current_offset.value = data.offset + data.limit
  } catch (error) {
    console.error('Failed to fetch puzzles:', error)
  } finally {
    loading_puzzles.value = false
  }
}

// Show puzzle definition modal
async function show_puzzle_definition(puzzle: any) {
  loading_definition.value = true
  show_definition_modal.value = true

  try {
    const { data } = await api.GET("/api/puzzle/definition/{puzzle_id}", {
      params: { path: { puzzle_id: puzzle.id }, query: { include_solution: true } },
    })
    selected_puzzle_definition.value = data as unknown as PuzzleDefinition
  } catch (error) {
    console.error('Failed to fetch puzzle definition:', error)
    selected_puzzle_definition.value = puzzle as PuzzleDefinition
  } finally {
    loading_definition.value = false
  }
}

function close_definition_modal() {
  show_definition_modal.value = false
  selected_puzzle_definition.value = null
}

// Watch for filter changes
watch(
  [
    () => store.puzzle_id,
    () => store.puzzle_types,
    () => store.puzzle_sizes,
    () => store.difficulties,
    () => store.has_attempts,
  ],
  () => {
    current_offset.value = 0
    fetch_puzzles(false)
  },
  { deep: true }
)

// Watch grid size changes
watch(grid_size, () => {
  current_offset.value = 0
  fetch_puzzles(false)
})

// Re-observe sentinel when it becomes available
watch(scroll_sentinel, (el) => {
  if (el && intersection_observer) {
    intersection_observer.observe(el)
  }
})

function setup_infinite_scroll() {
  if (intersection_observer) {
    intersection_observer.disconnect()
  }

  intersection_observer = new IntersectionObserver(
    (entries) => {
      const entry = entries[0]
      if (entry.isIntersecting && has_more.value && !loading_puzzles.value) {
        fetch_puzzles(true)
      }
    },
    { threshold: 0.1 }
  )

  if (scroll_sentinel.value) {
    intersection_observer.observe(scroll_sentinel.value)
  }
}

onMounted(() => {
  fetch_puzzles()
  setup_infinite_scroll()
})

onUnmounted(() => {
  if (intersection_observer) {
    intersection_observer.disconnect()
  }
})
</script>

<template>
  <div class="h-full">
  <div class="grid grid-cols-1 grid-rows-[auto_1fr] h-full gap-2 overflow-hidden">
    <!-- Header -->
    <Container class="flex flex-row items-center justify-between gap-2">
        <div class="text-sm text-gray-600">
          {{ displayed_puzzles.length }} of {{ total_count }} puzzles
        </div>

        <!-- Grid Size Control -->
        <div class="flex items-center space-x-2">
          <span class="text-sm text-gray-600">Grid size:</span>
          <select
            v-model="grid_size"
            class="px-3 py-1 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="small">Small</option>
            <option value="medium">Medium</option>
            <option value="large">Large</option>
          </select>
        </div>
    </Container>

    <!-- Puzzle Grid -->
    <Container class="p-4 h-full min-h-0 max-h-full overflow-y-auto">
      <!-- Loading State -->
      <div v-if="loading_puzzles && all_puzzles.length === 0" class="flex items-center justify-center h-64">
        <div class="text-xl text-gray-500">Loading puzzles...</div>
      </div>



      <!-- Grid -->
      <div v-else>
        <div class="grid gap-1 items-center" :class="grid_config.cols">
          <PuzzleBrowserItem
            v-for="puzzle in displayed_puzzles"
            :key="puzzle.id"
            :puzzle="puzzle"
            @click="show_puzzle_definition"
          />
        </div>

        <!-- Infinite scroll sentinel-->
        <div
          ref="scroll_sentinel"
          class="h-20 flex items-center justify-center"
        >
          <div v-if="loading_puzzles && all_puzzles.length > 0" class="text-gray-500">
            Loading more...
          </div>
          <div v-else-if="!has_more && all_puzzles.length > 0" class="text-gray-400 text-sm">
            End of results
          </div>
        </div>

<!--        &lt;!&ndash; No Results &ndash;&gt;-->
<!--        <div v-if="!loading_puzzles && displayed_puzzles.length === 0" class="text-center text-gray-500 mt-8">-->
<!--          No puzzles found with the selected filters.-->
<!--        </div>-->
      </div>
    </Container>
  </div>

  <!-- Puzzle Definition Modal -->
  <PuzzleDefinitionModal
    v-model="show_definition_modal"
    :puzzle="selected_puzzle_definition"
    :loading="loading_definition"
    @close="close_definition_modal"
  />
  </div>
</template>
