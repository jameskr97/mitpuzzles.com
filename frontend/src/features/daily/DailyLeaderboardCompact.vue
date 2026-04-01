<script setup lang="ts">
import { onMounted } from "vue";
import Container from "@/core/components/ui/Container.vue";
import { useDailyPuzzleStore } from "@/core/store/puzzle/useDailyPuzzleStore";

const daily_store = useDailyPuzzleStore();

const props = withDefaults(defineProps<{
  limit?: number;
}>(), {
  limit: 5,
});

onMounted(() => {
  daily_store.refreshLeaderboard();
});
</script>

<template>
  <Container class="flex flex-col">
    <div class="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">Daily Leaderboard</div>
    <div v-if="daily_store.leaderboard.length === 0" class="text-sm text-gray-400 text-center py-2">
      No entries yet.
    </div>
    <div v-else class="flex flex-col gap-0.5">
      <div
        v-for="entry in daily_store.leaderboard.slice(0, limit)"
        :key="entry.rank"
        class="flex items-center justify-between text-sm py-0.5"
        :class="entry.is_current_user ? 'font-bold' : ''"
      >
        <div class="flex items-center gap-2">
          <span class="text-gray-400 w-4 text-right">{{ entry.rank }}.</span>
          <span>{{ entry.username }}</span>
        </div>
        <span class="text-gray-500 tabular-nums">{{ entry.duration_display }}</span>
      </div>
    </div>
  </Container>
</template>
