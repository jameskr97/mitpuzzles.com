<script lang="ts" setup>
type StrNum = string | number;
defineProps<{
  events: StrNum[];
}>();
</script>

<template>
  <div class="w-full h-40 overflow-y-auto border border-amber-600">
    <ul class="list-disc pl-6">
      <!-- Render the newest event at the top -->
      <li v-for="(event, index) in [...events].reverse()" :key="index">
        {{ event }}
      </li>
    </ul>
  </div>
</template>
