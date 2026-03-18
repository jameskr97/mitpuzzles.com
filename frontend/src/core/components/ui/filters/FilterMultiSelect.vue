<script setup lang="ts">
import { computed } from 'vue'

export interface MultiSelectOption {
  value: string
  label?: string
  count?: number
  color?: string
  disabled?: boolean
}

defineProps<{
  label: string
  options: MultiSelectOption[]
}>()

const model = defineModel<Set<string>>({ default: () => new Set() })

const selected_count = computed(() => model.value.size)

const toggle_option = (value: string, disabled?: boolean) => {
  if (disabled) return

  const new_set = new Set(model.value)
  if (new_set.has(value)) {
    new_set.delete(value)
  } else {
    new_set.add(value)
  }
  model.value = new_set
}
</script>

<template>
  <div class="space-y-1">
    <div class="flex items-center justify-between">
      <h3 class="text-sm font-medium text-gray-700">{{ label }}</h3>
      <span v-if="selected_count > 0" class="text-xs text-blue-600 font-medium">
        {{ selected_count }} selected
      </span>
    </div>
    <div class="border border-gray-200 rounded-lg overflow-hidden">
      <div
        v-for="option in options"
        :key="option.value"
        class="relative flex items-center px-2.5 py-1.5 cursor-pointer transition-colors border-b border-gray-100 last:border-b-0 hover:bg-gray-50"
        :class="{
          'bg-blue-50 border-blue-200': model.has(option.value),
          'opacity-50 cursor-not-allowed': option.disabled || option.count === 0
        }"
        @click="toggle_option(option.value, option.disabled || option.count === 0)"
      >
        <!-- Checkmark indicator -->
        <div class="flex items-center justify-center w-3 h-3 mr-2">
          <svg
            v-if="model.has(option.value)"
            class="w-2.5 h-2.5 text-blue-600"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fill-rule="evenodd"
              d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
              clip-rule="evenodd"
            />
          </svg>
        </div>

        <!-- Label -->
        <span class="flex-1 text-xs font-medium text-gray-900 capitalize">
          {{ option.label || option.value }}
        </span>

        <!-- Count -->
        <span v-if="option.count !== undefined" class="text-xs text-gray-500 mr-2">
          {{ option.count }}
        </span>

        <!-- Color badge -->
        <div
          v-if="option.color"
          :class="option.color"
          class="w-2.5 h-2.5 rounded-full"
        />
      </div>
    </div>
  </div>
</template>
