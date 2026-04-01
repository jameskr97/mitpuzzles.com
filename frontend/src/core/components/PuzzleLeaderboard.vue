<script setup lang="ts">
import { watch } from "vue";
import { useAsyncState } from "@vueuse/core";
import Container from "@/core/components/ui/Container.vue";
import { api } from "@/core/services/client";
import type { LeaderboardEntry } from "@/core/types";

const props = defineProps<{
  puzzle_id: string;
}>();

const { state: entries, isLoading: loading, execute } = useAsyncState(
  async () => {
    const { data } = await api.GET("/api/puzzle/{puzzle_id}/leaderboard", {
      params: { path: { puzzle_id: props.puzzle_id } },
    });
    return ((data as any)?.leaderboard ?? []) as LeaderboardEntry[];
  },
  [] as LeaderboardEntry[],
  { resetOnExecute: false },
);

watch(() => props.puzzle_id, () => execute());
</script>

<template>
  <Container>
    <div class="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">Puzzle Leaderboard</div>
    <div v-if="loading" class="text-sm text-gray-400 text-center py-2">Loading...</div>
    <div v-else-if="entries.length === 0" class="text-sm text-gray-400 text-center py-2">No solves yet.</div>
    <div v-else class="flex flex-col gap-0.5">
      <div
        v-for="entry in entries"
        :key="entry.rank"
        class="flex items-center justify-between text-sm py-0.5 px-1"
        :class="entry.is_current_user ? 'font-bold' : ''"
      >
        <div class="flex items-center gap-2">
          <span class="text-gray-400 w-4 text-right">{{ entry.rank }}.</span>
          <span>{{ entry.username }}</span>
        </div>
        <span class="text-gray-500 tabular-nums">{{ entry.duration_display }}</span>
      </div>
    </div>
  </Container>
</template>
