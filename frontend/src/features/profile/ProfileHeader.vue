<script setup lang="ts">
import Container from "@/core/components/ui/Container.vue";
import { ACTIVE_GAMES } from "@/constants";

const props = defineProps<{
  username: string;
  is_own_profile: boolean;
  total_puzzles_solved: number;
  total_puzzles_attempted: number;
  solve_rate: number;
  current_streak: number;
  fastest_daily_count: number;
  puzzle_type_stats: { puzzle_type: string; solved_count: number }[];
}>();

function get_solved_count(puzzle_type: string): number {
  return props.puzzle_type_stats.find(e => e.puzzle_type === puzzle_type)?.solved_count ?? 0;
}

function get_game_icon(puzzle_type: string): string {
  return ACTIVE_GAMES[puzzle_type]?.icon ?? "🧩";
}

function capitalize(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1);
}
</script>

<template>
  <Container>
    <div class="flex items-center justify-between mb-2">
      <h1 class="text-2xl font-bold flex items-center gap-2">
        <span class="w-2.5 h-2.5 rounded-full bg-green-500 inline-block" />
        {{ username }}
      </h1>
      <router-link
        v-if="is_own_profile"
        :to="{ name: 'account' }"
        class="text-sm text-blue-600 hover:underline"
      >
        edit profile
      </router-link>
    </div>
    <div class="flex items-center justify-between text-sm border-t pt-2">
      <div class="flex items-center gap-6">
        <div class="flex flex-col items-center">
          <span class="text-lg font-bold">{{ total_puzzles_solved }}</span>
          <span class="text-gray-500 text-xs">Puzzles Solved</span>
        </div>
        <div class="flex flex-col items-center">
          <span class="text-lg font-bold">{{ solve_rate }}%</span>
          <span class="text-gray-500 text-xs">Solve Rate</span>
        </div>
        <div class="flex flex-col items-center">
          <span class="text-lg font-bold">{{ current_streak }}</span>
          <span class="text-gray-500 text-xs">Daily Streak</span>
        </div>
        <div class="flex flex-col items-center">
          <span class="text-lg font-bold">{{ fastest_daily_count }}</span>
          <span class="text-gray-500 text-xs">Fastest of Day</span>
        </div>
      </div>
      <div class="flex items-center gap-3">
        <router-link
          v-for="game_type in Object.keys(ACTIVE_GAMES)"
          :key="game_type"
          :to="'/' + game_type"
          class="flex flex-col items-center transition-colors"
          :class="get_solved_count(game_type) > 0
            ? 'text-gray-600 hover:text-gray-900'
            : 'text-gray-300 grayscale hover:text-gray-400'"
        >
          <span class="text-lg font-bold">{{ get_game_icon(game_type) }} {{ get_solved_count(game_type) }}</span>
          <span class="text-xs" :class="get_solved_count(game_type) > 0 ? 'text-gray-500' : 'text-gray-300'">{{ capitalize(game_type) }}</span>
        </router-link>
      </div>
    </div>
  </Container>
</template>
