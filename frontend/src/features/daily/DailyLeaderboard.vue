<script setup lang="ts">
/**
 * DailyLeaderboard - leaderboard for today's daily puzzle.
 * reads from the daily puzzle store (refreshed after solve in useDailyServices).
 */
import { onMounted, ref } from "vue";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/core/components/ui/table";
import Container from "@/core/components/ui/Container.vue";
import { Separator } from "@/core/components/ui/separator";
import { useDailyPuzzleStore } from "@/core/store/puzzle/useDailyPuzzleStore";

const daily_store = useDailyPuzzleStore();
const is_open = ref(true);

onMounted(() => {
  daily_store.refreshLeaderboard();
});
</script>

<template>
  <Container class="flex flex-col !bg-floralwhite">
    <div
      class="flex items-center justify-between cursor-pointer select-none w-full"
      @click="is_open = !is_open"
    >
      <div class="flex items-center">
        <v-icon name="ri-trophy-line" :scale="1.5" class="mr-2" />
        <span class="text-xl">{{ $t("freeplay:leaderboard.title") }}</span>
      </div>
      <v-icon
        name="md-keyboardarrowdown-round"
        :scale="1.5"
        :class="{ 'rotate-180': is_open }"
      />
    </div>

    <template v-if="is_open">
      <Separator class="mt-2 mb-1" />

      <div v-if="daily_store.leaderboard.length === 0" class="text-center text-gray-500 p-4">
        No entries yet. Be the first to solve today's puzzle!
      </div>
      <Table v-else>
        <TableHeader>
          <TableRow>
            <TableHead class="p-0">{{ $t("ui:table.rank") }}</TableHead>
            <TableHead>{{ $t("ui:table.time") }}</TableHead>
            <TableHead>{{ $t("ui:table.username") }}</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow
            v-for="(entry, index) in daily_store.leaderboard"
            :class="{ 'font-bold': entry.is_current_user }"
            :key="index"
          >
            <TableCell>{{ entry.rank }}</TableCell>
            <TableCell>{{ entry.duration_display }}</TableCell>
            <TableCell>{{ entry.username }}</TableCell>
          </TableRow>
        </TableBody>
      </Table>
    </template>
  </Container>
</template>
