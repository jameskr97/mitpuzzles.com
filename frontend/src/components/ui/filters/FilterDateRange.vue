<script setup lang="ts">
export interface DateRange {
  start: string
  end: string
}

defineProps<{
  label?: string
}>()

const model = defineModel<DateRange>({ default: () => ({ start: '', end: '' }) })
</script>

<template>
  <div class="space-y-1">
    <h3 v-if="label" class="text-sm font-medium text-gray-700">{{ label }}</h3>
    <div class="space-y-2">
      <div>
        <label class="block text-xs text-gray-600 mb-1">Start Date</label>
        <input
          :value="model.start"
          @input="model = { ...model, start: ($event.target as HTMLInputElement).value }"
          type="date"
          class="w-full px-2 py-1 text-xs border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
        />
      </div>
      <div>
        <label class="block text-xs text-gray-600 mb-1">End Date</label>
        <input
          :value="model.end"
          @input="model = { ...model, end: ($event.target as HTMLInputElement).value }"
          type="date"
          class="w-full px-2 py-1 text-xs border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
        />
      </div>
    </div>
  </div>
</template>
