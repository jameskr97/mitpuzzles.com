<script setup lang="ts">
import Container from "@/core/components/ui/Container.vue";
import { ACTIVE_GAMES } from "@/constants";

const props = defineProps<{
  total_puzzles_solved: number;
  total_puzzles_attempted: number;
  solve_rate: number;
  current_streak: number;
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
  <Container class="text-sm flex flex-col gap-1">
    <div class="flex justify-between">
      <span class="text-gray-500">Puzzles Solved</span>
      <span class="font-medium">{{ total_puzzles_solved }}</span>
    </div>
    <div class="flex justify-between">
      <span class="text-gray-500">Attempted</span>
      <span class="font-medium">{{ total_puzzles_attempted }}</span>
    </div>
    <div class="flex justify-between">
      <span class="text-gray-500">Solve Rate</span>
      <span class="font-medium">{{ solve_rate }}%</span>
    </div>
    <div class="flex justify-between">
      <span class="text-gray-500">Daily Streak</span>
      <span class="font-medium">{{ current_streak }}</span>
    </div>
    <div class="border-t pt-3 flex flex-col gap-1">
      <div
        v-for="entry in puzzle_type_stats"
        :key="entry.puzzle_type"
        class="flex justify-between text-xs"
        :class="entry.solved_count > 0 ? 'text-gray-600' : 'text-gray-300'"
      >
        <span>{{ get_game_icon(entry.puzzle_type) }} {{ capitalize(entry.puzzle_type) }}</span>
        <span class="font-medium">{{ entry.solved_count }}</span>
      </div>
    </div>
  </Container>
</template>
