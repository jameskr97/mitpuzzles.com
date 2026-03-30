<script setup lang="ts">
import Container from "@/core/components/ui/Container.vue";

const props = defineProps<{
  member_since: string;
  total_time_seconds: number;
  daily_streak: {
    current_streak: number;
    longest_streak: number;
    total_dailies_solved: number;
    fastest_daily_count: number;
  };
}>();

function format_member_since(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" });
}

function format_duration(seconds: number): string {
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  if (days > 0) return `${days} days, ${hours} hours`;
  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${minutes}m`;
}
</script>

<template>
  <Container class="text-sm flex flex-col gap-3">
    <div>
      <div class="text-gray-500">Member since</div>
      <div>{{ format_member_since(member_since) }}</div>
    </div>
    <div>
      <div class="text-gray-500">Time spent solving</div>
      <div>{{ format_duration(total_time_seconds) }}</div>
    </div>
    <div class="border-t pt-3">
      <div class="font-semibold mb-1">Daily Challenge</div>
      <div class="flex flex-col gap-1 text-xs">
        <div class="flex justify-between">
          <span class="text-gray-500">Current streak</span>
          <span class="font-medium">{{ daily_streak.current_streak }} days</span>
        </div>
        <div class="flex justify-between">
          <span class="text-gray-500">Longest streak</span>
          <span class="font-medium">{{ daily_streak.longest_streak }} days</span>
        </div>
        <div class="flex justify-between">
          <span class="text-gray-500">Dailies solved</span>
          <span class="font-medium">{{ daily_streak.total_dailies_solved }}</span>
        </div>
        <div class="flex justify-between">
          <span class="text-gray-500">Fastest of day</span>
          <span class="font-medium">{{ daily_streak.fastest_daily_count }}x</span>
        </div>
      </div>
    </div>
  </Container>
</template>
