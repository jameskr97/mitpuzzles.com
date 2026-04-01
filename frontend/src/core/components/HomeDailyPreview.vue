<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from "vue";
import HomePuzzlePreview from "@/core/components/HomePuzzlePreview.vue";
import { ACTIVE_GAMES } from "@/constants";
import { useDailyPuzzleStore } from "@/core/store/puzzle/useDailyPuzzleStore";
import { useAuthStore } from "@/core/store/useAuthStore";

const dailyStore = useDailyPuzzleStore();
const authStore = useAuthStore();
const is_dev = import.meta.env.DEV;

const visible_games = computed(() =>
  Object.values(ACTIVE_GAMES).filter((g) => !g.admin_only || authStore.isAdmin || is_dev),
);

// cycle through puzzle previews when unsolved
const preview_index = ref(0);
const preview_game = computed(() => visible_games.value[preview_index.value]);
let cycle_timer: ReturnType<typeof setInterval> | null = null;

onMounted(() => {
  cycle_timer = setInterval(() => {
    if (!dailyStore.daily?.puzzle.is_solved) {
      preview_index.value = (preview_index.value + 1) % visible_games.value.length;
    }
  }, 750);
});

onUnmounted(() => {
  if (cycle_timer) clearInterval(cycle_timer);
});
</script>

<template>
  <HomePuzzlePreview v-if="preview_game" title="Daily Puzzle" page="daily">
    <div class="relative w-full aspect-square">
      <div
        class="absolute inset-0"
        :class="dailyStore.daily?.puzzle.is_solved ? 'opacity-40 blur-[1px]' : 'blur-[2px] opacity-60'"
      >
        <component
          v-if="dailyStore.solved_state && dailyStore.game_entry"
          :is="dailyStore.game_entry.component"
          :state="dailyStore.solved_state"
        />
        <component
          v-else
          :is="preview_game.component"
          :state="preview_game.default"
        />
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
