<script setup lang="ts">
import { computed } from 'vue'
import { FilterMultiSelect, type MultiSelectOption } from '@/core/components/ui/filters'

const props = defineProps<{
  label?: string
  options: { value: string; count?: number }[]
}>()

const model = defineModel<Set<string>>({ default: () => new Set() })

// Color mapping for puzzle types
const puzzle_colors: Record<string, string> = {
  minesweeper: 'bg-gray-500',
  sudoku: 'bg-blue-500',
  tents: 'bg-green-500',
  kakurasu: 'bg-purple-500',
  lightup: 'bg-yellow-400',
  nonograms: 'bg-red-500',
  battleships: 'bg-slate-700',
  mosaic: 'bg-orange-500',
}

// Transform options to include colors
const options_with_colors = computed<MultiSelectOption[]>(() => {
  return props.options.map(opt => ({
    value: opt.value,
    label: opt.value.charAt(0).toUpperCase() + opt.value.slice(1),
    count: opt.count,
    color: puzzle_colors[opt.value] || 'bg-gray-400',
  }))
})
</script>

<template>
  <FilterMultiSelect
    v-model="model"
    :label="label ?? 'Puzzle Types'"
    :options="options_with_colors"
  />
</template>
