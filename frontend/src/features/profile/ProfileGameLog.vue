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
  <Container>
    <div class="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">Recent Games</div>
    <div v-if="games.length === 0" class="text-sm text-gray-400 text-center py-4">no games yet</div>
    <div v-else class="flex flex-col">
      <div
        v-for="(game, i) in games"
        :key="i"
        class="flex items-center gap-2 py-1 px-1 border-b border-gray-100 last:border-0"
      >
        <span class="text-sm">{{ get_game_icon(game.puzzle_type) }}</span>
        <span class="text-sm font-medium">{{ capitalize(game.puzzle_type) }}</span>
        <span class="text-xs text-gray-400">{{ game.puzzle_size }}</span>
        <span class="flex-1"></span>
        <span class="text-xs text-gray-400">{{ game.date }}</span>
        <span
          class="text-sm font-semibold w-12 text-right"
          :class="game.solved ? 'text-green-600' : 'text-red-400'"
        >
          {{ game.solved ? format_time(game.time) : 'DNF' }}
        </span>
      </div>
    </div>
  </Container>
</template>
