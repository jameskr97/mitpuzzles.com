<script setup lang="ts">
import { computed, defineAsyncComponent, provide, onErrorCaptured } from "vue";
import { useDailyPuzzleStore } from "@/core/store/puzzle/useDailyPuzzleStore";
import { ACTIVE_GAMES } from "@/constants";
import Container from "@/core/components/ui/Container.vue";

const daily_store = useDailyPuzzleStore();
daily_store.init();

provide("puzzle-type-override", "daily");

onErrorCaptured((err) => {
  console.error("DailyPuzzle caught error:", err);
  return false;
});

const freeplay_component = computed(() => {
  const type = daily_store.puzzle_type;
  if (!type || !ACTIVE_GAMES[type]) return null;
  return defineAsyncComponent(ACTIVE_GAMES[type].freeplay);
});
</script>

<template>
  <div>
    <Container v-if="daily_store.loading" class="flex justify-center py-20">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
    </Container>

    <Container v-else-if="daily_store.error" class="text-center py-20">
      <p class="text-gray-500">{{ daily_store.error }}</p>
    </Container>

    <!-- show error if puzzle type not in ACTIVE_GAMES -->
    <Container v-else-if="daily_store.is_ready && !freeplay_component" class="text-center py-20">
      <p class="text-gray-500">{{ daily_store.puzzle_type }} is not available yet.</p>
    </Container>

    <Suspense v-else-if="daily_store.is_ready">
      <div><component :is="freeplay_component" /></div>
      <template #fallback>
        <Container class="flex justify-center py-20">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
        </Container>
      </template>
    </Suspense>
  </div>
</template>
