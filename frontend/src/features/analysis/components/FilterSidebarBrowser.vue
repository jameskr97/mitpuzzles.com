<script setup lang="ts">
import { onMounted } from 'vue'
import { useAnalysisStore } from '@/features/analysis/stores/useAnalysisStore'
import FilterPuzzleSelector from '@/features/analysis/components/FilterPuzzleSelector.vue'
import { FilterMultiSelect, FilterRadioGroup } from '@/components/ui/filters'
import { Input } from '@/components/ui/input'

const store = useAnalysisStore()

onMounted(() => {
  if (!store.options) {
    store.fetch_options()
  }
})
</script>

<template>
  <div class="space-y-4">
    <!-- Puzzle ID Lookup -->
    <div class="space-y-1">
      <label class="text-sm font-medium text-gray-700">Puzzle ID</label>
      <Input
        v-model="store.puzzle_id"
        placeholder="Enter puzzle ID..."
        class="text-xs"
      />
    </div>

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

    <!-- Has Attempts -->
    <FilterRadioGroup
      v-model="store.has_attempts"
      label="Attempts"
      :options="[
        { value: 'all', label: 'All Puzzles' },
        { value: 'with_attempts', label: 'Has Attempts' },
        { value: 'without_attempts', label: 'No Attempts' },
      ]"
    />
  </div>
</template>
