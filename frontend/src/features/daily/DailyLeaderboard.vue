<script setup lang="ts">
/**
 * DailyLeaderboard - Leaderboard for daily challenge puzzles.
 * Reads from the daily puzzle store (refreshed after solve in useDailyServices).
 */
import { computed, onMounted, ref } from "vue";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/core/components/ui/table";
import Container from "@/core/components/ui/Container.vue";
import { Separator } from "@/core/components/ui/separator";
import { useDailyPuzzleStore } from "@/core/store/puzzle/useDailyPuzzleStore";

const props = defineProps<{
  puzzle_type: string;
  date: string;
}>();

const daily_store = useDailyPuzzleStore();
const is_open = ref(true);

const entries = computed(() => daily_store.getDailyLeaderboard(props.date, props.puzzle_type));

onMounted(() => {
  daily_store.refreshDailyLeaderboard(props.date, props.puzzle_type);
});
</script>

<template>
  <Container class="flex flex-col !bg-floralwhite">
    <div class="flex items-center justify-between cursor-pointer select-none w-full">
      <div class="flex items-center">
        <v-icon name="ri-trophy-line" :scale="1.5" class="mr-2" />
        <span class="text-xl">{{ $t("daily:title") }} Leaderboard</span>
      </div>
      <v-icon
        name="md-keyboardarrowdown-round"
        :scale="1.5"
        :class="{ 'rotate-180': is_open }"
        @click="is_open = !is_open"
      />
    </div>

    <template v-if="is_open">
      <Separator class="mt-2 mb-1" />
      <div v-if="entries.length === 0" class="text-center text-gray-500 p-4">
        No entries yet. Be the first to solve today's {{ puzzle_type }}!
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
            v-for="(entry, index) in entries"
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
