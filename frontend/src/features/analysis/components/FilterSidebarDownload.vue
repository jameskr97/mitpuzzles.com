<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useAnalysisStore } from '@/features/analysis/stores/useAnalysisStore'
import FilterPuzzleSelector from '@/features/analysis/components/FilterPuzzleSelector.vue'
import { FilterMultiSelect, FilterRadioGroup, FilterDateRange } from '@/core/components/ui/filters'

const store = useAnalysisStore()

const date_range = computed({
  get: () => ({ start: store.date_start, end: store.date_end }),
  set: (val) => { store.date_start = val.start; store.date_end = val.end },
})

const solved_options = [
  { value: 'all', label: 'All Attempts' },
  { value: 'solved', label: 'Solved Only' },
  { value: 'unsolved', label: 'Unsolved Only' },
]

onMounted(() => {
  if (!store.options) {
    store.fetch_options()
  }
})
</script>

<template>
  <div class="space-y-4">
    <!-- Puzzle Types -->
    <FilterPuzzleSelector
      v-model="store.puzzle_types"
      :options="store.options?.puzzle_types ?? []"
    />

    <!-- Puzzle Sizes -->
    <FilterMultiSelect
      v-model="store.puzzle_sizes"
      label="Puzzle Sizes"
      :options="store.options?.puzzle_sizes ?? []"
    />

    <!-- Difficulty -->
    <FilterMultiSelect
      v-model="store.difficulties"
      label="Difficulty"
      :options="store.options?.puzzle_difficulties ?? []"
    />

    <!-- Solved Filter -->
    <FilterRadioGroup
      v-model="store.solved_filter"
      label="Completion Status"
      :options="solved_options"
    />

    <FilterDateRange v-model="date_range" label="Date Played" />
  </div>
</template>
