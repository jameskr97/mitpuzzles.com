<script setup lang="ts">
defineProps<{
  label: string
}>()

const model = defineModel<boolean>({ default: false })
</script>

<template>
  <div class="space-y-1">
    <div class="border border-gray-200 rounded-lg overflow-hidden">
      <label
        class="relative flex items-center px-2.5 py-1.5 cursor-pointer transition-colors hover:bg-gray-50"
        :class="{ 'bg-blue-50': model }"
      >
        <input
          v-model="model"
          type="checkbox"
          class="h-3 w-3 text-blue-600 focus:ring-blue-500 border-gray-300 rounded mr-2"
        />
        <span class="text-xs font-medium text-gray-900">
          {{ label }}
        </span>
      </label>
    </div>
  </div>
</template>
