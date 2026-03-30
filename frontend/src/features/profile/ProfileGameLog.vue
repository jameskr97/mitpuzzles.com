<script setup lang="ts">
import Container from "@/core/components/ui/Container.vue";
import { ACTIVE_GAMES } from "@/constants";

const props = defineProps<{
  games: {
    attempt_id: string;
    puzzle_type: string;
    puzzle_size: string;
    puzzle_difficulty: string | null;
    time: number | null;
    solved: boolean;
    date: string;
  }[];
}>();

function get_game_icon(puzzle_type: string): string {
  return ACTIVE_GAMES[puzzle_type]?.icon ?? "🧩";
}

function capitalize(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

function format_time(seconds: number | null): string {
  if (seconds === null) return "-";
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, "0")}`;
}
</script>

<template>
  <Container class="col-span-2">
    <div class="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">Recent Games</div>
    <div v-if="games.length === 0" class="text-sm text-gray-400 text-center py-4">no games yet</div>
    <div v-else class="flex flex-col gap-2">
      <div
        v-for="(game, i) in games"
        :key="i"
        class="flex items-center gap-3 p-2 rounded border border-gray-100 hover:border-gray-200 transition-colors"
      >
        <div class="w-10 h-10 shrink-0 flex items-center justify-center text-2xl">
          {{ get_game_icon(game.puzzle_type) }}
        </div>
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-1.5">
            <span>{{ get_game_icon(game.puzzle_type) }}</span>
            <span class="text-sm font-medium">{{ capitalize(game.puzzle_type) }}</span>
            <span class="text-xs text-gray-400">{{ game.puzzle_size }} {{ game.puzzle_difficulty }}</span>
          </div>
          <div class="text-xs text-gray-400 mt-0.5">{{ game.date }}</div>
        </div>
        <div class="shrink-0 text-right">
          <div
            class="text-sm font-semibold"
            :class="game.solved ? 'text-green-600' : 'text-red-400'"
          >
            {{ game.solved ? format_time(game.time) : 'DNF' }}
          </div>
          <div class="text-xs" :class="game.solved ? 'text-green-500' : 'text-red-300'">
            {{ game.solved ? 'solved' : 'abandoned' }}
          </div>
        </div>
      </div>
    </div>
  </Container>
</template>
