<script setup lang="ts">
import { onMounted, ref, reactive } from "vue";
import Container from "@/core/components/ui/Container.vue";
import { useDailyPuzzleStore } from "@/core/store/puzzle/useDailyPuzzleStore";
import { ACTIVE_GAMES } from "@/constants.ts";

const dailyStore = useDailyPuzzleStore();

// Puzzle definitions keyed by puzzle_type, used to render canvas previews
const definitions = reactive<Record<string, any>>({});

onMounted(async () => {
  await dailyStore.ensureFresh();

  // Fetch all definitions in parallel for previews
  const fetches = dailyStore.puzzles.map(async (p) => {
    try {
      const def = await dailyStore.fetchDailyDefinition(dailyStore.today_date, p.puzzle_type);
      definitions[p.puzzle_type] = {
        definition: def,
        board: def.initial_state,
      };
    } catch {
      // Silently fail — card will just show without preview
    }
  });
  await Promise.all(fetches);
});

function getStatus(puzzle_type: string) {
  return dailyStore.puzzles.find((p) => p.puzzle_type === puzzle_type);
}
</script>

<template>
  <div class="flex flex-col gap-2">
    <div class="w-full max-w-4xl mx-auto">
      <div v-if="dailyStore.loading" class="text-center text-gray-500 p-8">
        Loading...
      </div>
      <div v-else class="grid grid-cols-2 md:grid-cols-3 gap-2">
        <router-link
          v-for="game in Object.values(ACTIVE_GAMES)"
          :key="game.key"
          :to="{ name: 'daily-' + game.key }"
          class="block"
        >
          <Container
            class="overflow-hidden hover:-translate-y-0.5 transition-all duration-200 mb-0 pb-0 cursor-pointer"
            :class="getStatus(game.key)?.is_solved ? 'border-green-400 border-2' : ''"
          >
            <div class="flex flex-col gap-1">
              <!-- Puzzle preview canvas -->
              <div class="overflow-hidden min-w-0">
                <div class="@container aspect-square box-border place-items-center grid select-none pointer-events-none rounded-xs overflow-hidden">
                  <component
                    v-if="definitions[game.key]"
                    :is="game.component"
                    :state="definitions[game.key]"
                  />
                  <span v-else class="text-4xl">{{ game.icon }}</span>
                </div>
              </div>
            </div>

            <div class="text-center mt-1">{{ game.name }}</div>
          </Container>
        </router-link>
      </div>
    </div>
  </div>
</template>
