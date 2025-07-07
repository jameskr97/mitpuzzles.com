<script setup lang="ts">
import { inject, watch, computed } from "vue";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import Container from "@/components/ui/Container.vue";
import type { PuzzleController } from "@/services/game/engines/types.ts";
import { useGameMetadataStore } from "@/store/useGameMetadataStore.ts";
import { useFreeplayLeaderboardStore } from "@/store/useFreeplayLeaderboardStore.ts";

const puzzle = inject<PuzzleController>("puzzle")!;
const puzzle_type = puzzle.state_puzzle.value.definition.puzzle_type;

const metaStore = useGameMetadataStore();
const current_variant = computed(() => metaStore.getSelectedVariant(puzzle_type));
const size = computed(() => current_variant.value[0]);
const difficulty = computed(() => current_variant.value[1]);

const leaderStore = useFreeplayLeaderboardStore();

watch(() => metaStore.getSelectedVariant(puzzle_type), async (newVariant) => {
  await leaderStore.refreshLeaderboard(puzzle_type, newVariant[0], newVariant[1]);
}, { immediate: true });
</script>

<template>
  <Container class="rounded shadow w-full p-2">
    <div class="text-xl">Leaderboard</div>
    <div class="divider m-0"></div>
    {{leaderStore.leaderboardEntryCount(puzzle_type, size, difficulty)}}
    {{ puzzle_type }} {{ size }} {{ difficulty }}
    <div v-if="leaderStore.leaderboardEntryCount(puzzle_type, size, difficulty) === 0" class="text-center text-gray-500 p-4 w-full">
      No entries yet for the {{ size }} {{ puzzle_type }} with difficulty
      {{ difficulty }}.
    </div>
    <Table v-else>
      <TableHeader>
        <TableRow>
          <TableHead class="p-0"> Rank</TableHead>
          <TableHead>Time</TableHead>
          <TableHead>Username</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        <TableRow v-for="(entry, index) in leaderStore.getLeaderboard(puzzle_type, size, difficulty)" :key="index">
          <TableCell>{{ entry.rank }}</TableCell>
          <TableCell>{{ entry.duration_display }}</TableCell>
          <TableCell>{{ entry.username }}</TableCell>
        </TableRow>
      </TableBody>
    </Table>

    <!--    <table v-else class="table table-xs w-full">-->
    <!--      <thead>-->
    <!--        <tr>-->
    <!--          <th>Rank</th>-->
    <!--          <th>Time</th>-->
    <!--          <th>Username</th>-->
    <!--        </tr>-->
    <!--      </thead>-->
    <!--      <tbody>-->
    <!--        <tr v-for="(entry, index) in leaderboard.leaderboard" :key="index">-->
    <!--          <th>{{entry.rank}}</th>-->
    <!--          <td>{{entry.duration_display}}</td>-->
    <!--          <td>{{entry.username}}</td>-->
    <!--        </tr>-->
    <!--      </tbody>-->
    <!--    </table>-->
  </Container>
</template>

<style scoped></style>
