<script setup lang="ts">
import { useRoute } from "vue-router";
import { getLeaderboard } from "@/services/app.ts";
import { onMounted, ref, watch } from "vue";
import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import Container from "@/components/ui/Container.vue";
import { usePuzzleController } from "@/composables/usePuzzleController.ts";
import type { SupportedPuzzleTypes } from "@/codegen/websocket/game.schema"

const route = useRoute();
const puzzle = usePuzzleController(route.meta.game_type as SupportedPuzzleTypes);

const leaderboard = ref<Awaited<ReturnType<typeof getLeaderboard>> | null>(null);
const update_leaderboard = async () => {
  const [size, diff] = puzzle.selected_variant.value;
  const data = await getLeaderboard(puzzle.puzzleType, size, diff);
  leaderboard.value = data.data
};
puzzle.bus.on("submit_result", update_leaderboard);
watch(() => puzzle.selected_variant.value, update_leaderboard);
onMounted(update_leaderboard);
</script>

<template>
  <Container class="rounded shadow w-full p-2">
    <div class="text-xl">Leaderboard</div>
    <div class="divider m-0"></div>
    <div v-if="!leaderboard">
      <div class="text-center text-gray-500 p-4">
        Loading leaderboard...
      </div>
    </div>
    <div v-else-if="leaderboard.count === 0" class="text-center text-gray-500 p-4 w-full">
      No entries yet for the {{puzzle.selected_variant.value[0]}} {{puzzle.puzzle_type}} with difficulty {{puzzle.selected_variant.value[1]}}.
    </div>
    <Table v-else>
      <TableHeader>
        <TableRow>
          <TableHead class="p-0">
            Rank
          </TableHead>
          <TableHead>Time</TableHead>
          <TableHead>Username</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        <TableRow v-for="(entry, index) in leaderboard.leaderboard" :key="index">
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
