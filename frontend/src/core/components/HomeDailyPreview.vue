<script setup lang="ts">
import HomePuzzlePreview from "@/core/components/HomePuzzlePreview.vue";
import { useDailyPuzzleStore } from "@/core/store/puzzle/useDailyPuzzleStore";

const dailyStore = useDailyPuzzleStore();
</script>

<template>
  <HomePuzzlePreview title="Daily Puzzle" page="daily" container-class="h-full" title-class="text-xl">
    <div class="relative w-full aspect-square bg-gray-100 rounded">
      <div
        v-if="dailyStore.daily?.puzzle.is_solved && dailyStore.solved_state && dailyStore.game_entry"
        class="absolute inset-0 opacity-40 blur-[1px]"
      >
        <component :is="dailyStore.game_entry.component" :state="dailyStore.solved_state" />
      </div>

      <div class="absolute inset-0 flex flex-col items-center justify-center gap-1">
        <template v-if="dailyStore.daily?.puzzle.is_solved">
          <span class="text-5xl">✅</span>
          <span class="text-lg font-bold text-green-700">{{ dailyStore.daily.puzzle.completion_time }}</span>
        </template>
        <template v-else>
          <span class="text-8xl drop-shadow-lg">❓</span>
        </template>
      </div>
    </div>
  </HomePuzzlePreview>
</template>
