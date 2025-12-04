import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import { api } from '@/core/services/axios'

export interface FilterOption {
  value: string
  count: number
}

export interface FilterOptions {
  puzzle_types: FilterOption[]
  puzzle_sizes: FilterOption[]
  puzzle_difficulties: FilterOption[]
  attempts_options: FilterOption[]
}

export const useAnalysisStore = defineStore('analysis', () => {
  // === Scope ===
  const scope = ref<'device' | 'user'>('device')
  const selected_entity_id = ref<string | null>(null)

  // === Active tab ===
  const active_tab = ref<'analytics' | 'download' | 'browser'>('analytics')

  // === Filter selections ===
  const puzzle_id = ref<string>('')
  const puzzle_types = ref<Set<string>>(new Set())
  const puzzle_sizes = ref<Set<string>>(new Set())
  const difficulties = ref<Set<string>>(new Set())
  const has_attempts = ref<'all' | 'with_attempts' | 'without_attempts'>('all')
  const solved_filter = ref<'all' | 'solved' | 'unsolved'>('all')

  // === Dynamic options from API ===
  const options = ref<FilterOptions | null>(null)
  const loading_options = ref(false)

  // === Actions ===
  async function fetch_options() {
    loading_options.value = true
    try {
      const params: Record<string, string | string[]> = {}

      if (puzzle_types.value.size > 0) {
        params.puzzle_type = [...puzzle_types.value]
      }
      if (puzzle_sizes.value.size > 0) {
        params.puzzle_size = [...puzzle_sizes.value]
      }
      if (difficulties.value.size > 0) {
        params.puzzle_difficulty = [...difficulties.value]
      }
      if (has_attempts.value !== 'all') {
        params.has_attempts = has_attempts.value
      }

      // Add entity filter based on scope
      if (selected_entity_id.value) {
        if (scope.value === 'user') {
          params.filter_user_id = selected_entity_id.value
        } else if (scope.value === 'device') {
          params.filter_device_id = selected_entity_id.value
        }
      }

      const response = await api.get('/api/puzzle/filter-options', {
        params,
        paramsSerializer: { indexes: null },
      })
      options.value = response.data
    } catch (error) {
      console.error('Failed to fetch filter options:', error)
    } finally {
      loading_options.value = false
    }
  }

  function clear_all() {
    puzzle_id.value = ''
    puzzle_types.value = new Set()
    puzzle_sizes.value = new Set()
    difficulties.value = new Set()
    has_attempts.value = 'all'
    solved_filter.value = 'all'
    selected_entity_id.value = null
  }

  // Refetch options when filters or entity selection change
  watch(
    [
      () => puzzle_types.value,
      () => puzzle_sizes.value,
      () => difficulties.value,
      () => scope.value,
      () => selected_entity_id
    ],
    () => {
      console.log("user changed")
      fetch_options()
    },
    { deep: true }
  )

  return {
    // State
    scope,
    selected_entity_id,
    active_tab,
    puzzle_id,
    puzzle_types,
    puzzle_sizes,
    difficulties,
    has_attempts,
    solved_filter,
    options,
    loading_options,
    // Actions
    fetch_options,
    clear_all,
  }
})
