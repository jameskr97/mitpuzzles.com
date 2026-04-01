<script setup lang="ts">
import Container from "@/core/components/ui/Container.vue";
import { ACTIVE_GAMES } from "@/constants.ts";
import { watch } from "vue";
import { useAsyncState } from "@vueuse/core";
import { api } from "@/core/services/client.ts";
import type { RecentGameEntry } from "@/core/types.ts";

const props = defineProps({
  num_games: { type: Number, default: 8, required: false },
});

const {
  state: games,
  execute: refresh,
} = useAsyncState(
  async () => {
    const { data } = await api.GET("/api/puzzle/graphs/recent-games", {
      params: { query: { limit: props.num_games } },
    });
    return (data ?? []) as RecentGameEntry[];
  },
  [] as RecentGameEntry[],
  { resetOnExecute: false },
);
watch(
  () => props.num_games,
  () => refresh(),
);
</script>

<template>
  <Container class="flex flex-col">
    <div class="text-xs font-semibold text-gray-400 uppercase mb-2">Recent Puzzle Submissions</div>
    <div class="grid gap-3 w-full" :style="{ gridTemplateColumns: `repeat(${num_games}, 1fr)` }">
      <router-link
        v-for="game in games"
        :key="game.attempt_id"
        :to="{ name: 'game-playback', params: { attempt_id: game.attempt_id } }"
        class="flex flex-col border p-0.5 overflow-hidden hover:shadow-md transition-shadow bg-white"
      >
        <div class="aspect-square pointer-events-none select-none">
          <component
            v-if="ACTIVE_GAMES[game.puzzle_type]"
            :is="ACTIVE_GAMES[game.puzzle_type].component"
            :state="{
              definition: game.definition,
              board: game.board_state,
            }"
          />
        </div>
        <div class="px-2 py-1.5 border-t bg-gray-50">
          <div class="flex items-center justify-between">
            <span class="text-xs font-medium truncate">{{ game.username ?? "Anonymous" }}</span>
            <span
              class="text-xs font-semibold tabular-nums"
              :class="game.is_solved ? 'text-green-600' : 'text-red-400'"
            >
              {{ game.is_solved && game.time ? game.time.toFixed(1) + "s" : "DNF" }}
            </span>
          </div>
          <div class="flex items-center justify-between mt-0.5">
            <span class="text-[10px] text-gray-400">{{ game.puzzle_type }} {{ game.puzzle_size }}</span>
            <span
              v-if="game.metrics?.efficiency != null"
              class="text-[10px] tabular-nums"
              :class="
                game.metrics.efficiency >= 0.8
                  ? 'text-green-500'
                  : game.metrics.efficiency >= 0.5
                    ? 'text-amber-500'
                    : 'text-red-400'
              "
            >
              {{ Math.round(game.metrics.efficiency * 100) }}%
            </span>
          </div>
        </div>
      </router-link>
    </div>
  </Container>
</template>

<style scoped></style>
