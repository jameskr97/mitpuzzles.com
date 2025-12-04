<script setup lang="ts">
export interface FilterOption {
  value: string
  label: string
  count?: number
}

defineProps<{
  label: string
  options: FilterOption[]
}>()

const model = defineModel<string>({ required: true })
</script>

<template>
  <div class="space-y-1">
    <h3 class="text-sm font-medium text-gray-700">{{ label }}</h3>
    <div class="border border-gray-200 rounded-lg overflow-hidden">
      <div
        v-for="option in options"
        :key="option.value"
        class="relative flex items-center px-2.5 py-1.5 cursor-pointer transition-colors border-b border-gray-100 last:border-b-0 hover:bg-gray-50"
        :class="{ 'bg-blue-50 border-blue-200': model === option.value }"
        @click="model = option.value"
      >
        <div class="flex items-center justify-center w-3 h-3 mr-2">
          <div
            v-if="model === option.value"
            class="w-2 h-2 bg-blue-600 rounded-full"
          />
        </div>
        <span class="flex-1 text-xs font-medium text-gray-900">
          {{ option.label }}
        </span>
        <span v-if="option.count !== undefined" class="text-xs text-gray-500">
          {{ option.count }}
        </span>
      </div>
    </div>
  </div>
</template>
