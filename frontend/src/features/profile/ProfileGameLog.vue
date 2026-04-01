<script setup lang="ts">
import { computed } from "vue";
import Container from "@/core/components/ui/Container.vue";
import { ACTIVE_GAMES } from "@/constants";

const props = defineProps<{
  games: {
    attempt_id: string | null;
    puzzle_type: string;
    puzzle_size: string;
    puzzle_difficulty: string | null;
    time: number | null;
    solved: boolean;
    status: string; // "solved", "abandoned", "skipped"
    skip_count?: number | null;
    date: string;
    actual_actions?: number | null;
    efficiency?: number | null;
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
      <template v-for="(game, i) in games" :key="i">
        <!-- collapsed skip group -->
        <div
          v-if="game.status === 'skipped'"
          class="flex items-center py-1 px-1 border-b border-gray-100 last:border-0 text-xs text-gray-300 italic"
        >
          skipped {{ game.skip_count }} puzzle{{ game.skip_count !== 1 ? 's' : '' }} without trying
        </div>

        <!-- normal game entry -->
        <component
          v-else
          :is="game.attempt_id ? 'router-link' : 'div'"
          :to="game.attempt_id ? { name: 'game-playback', params: { attempt_id: game.attempt_id } } : undefined"
          class="flex items-center gap-2 py-1 px-1 border-b border-gray-100 last:border-0 rounded"
          :class="game.attempt_id ? 'hover:bg-gray-50 transition-colors cursor-pointer' : ''"
        >
          <span class="text-sm">{{ get_game_icon(game.puzzle_type) }}</span>
          <span class="text-sm font-medium">{{ capitalize(game.puzzle_type) }}</span>
          <span class="text-xs text-gray-400">{{ game.puzzle_size }}</span>
          <span class="flex-1"></span>
          <span v-if="game.actual_actions != null" class="text-xs text-gray-400 tabular-nums">
            <span class="inline-block w-6 text-right">{{ game.actual_actions }}</span> clicks,
            efficiency <span class="inline-block w-7 text-right" :class="(game.efficiency ?? 0) >= 0.8 ? 'text-green-500' : (game.efficiency ?? 0) >= 0.5 ? 'text-amber-500' : 'text-red-400'">{{ Math.round((game.efficiency ?? 0) * 100) }}%</span>
          </span>
          <span class="text-sm font-semibold w-12 text-right" :class="{
            'text-green-600': game.status === 'solved',
            'text-red-400': game.status === 'abandoned',
          }">
            {{ game.status === 'solved' ? format_time(game.time) : 'DNF' }}
          </span>
        </component>
      </template>
    </div>
  </Container>
</template>
