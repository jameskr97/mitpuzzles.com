<script setup lang="ts">
import { ref } from "vue";
import { format_game_stopwatch } from "@/lib/util";

// Get current time and update every second
const time_current = ref(Date.now());
setInterval(() => (time_current.value = Date.now()), 1000);

defineProps({
  timeReceived: { type: Number, required: true },
  timeCompleted: { type: Number, required: false },
});
</script>

<template>
  <div class="text-2xl text-right">
    <span v-if="timeCompleted" class="text-green-500">{{ format_game_stopwatch(timeCompleted - timeReceived) }}</span>
    <span v-else>{{ format_game_stopwatch(time_current - timeReceived) }}</span>
  </div>
</template>
