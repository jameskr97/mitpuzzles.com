<script setup lang="ts">
import { inject, watch, computed, ref } from "vue";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import Container from "@/components/ui/Container.vue";
import type { PuzzleController } from "@/services/game/engines/types.ts";
import { usePuzzleMetadataStore } from "@/store/puzzle/usePuzzleMetadataStore.ts";
import { usePuzzleLeaderboardStore } from "@/store/puzzle/usePuzzleLeaderboardStore.ts";
import { Separator } from "@/components/ui/separator";

const puzzle = inject<PuzzleController>("puzzle")!;
const puzzle_type = puzzle.state_puzzle.value.definition.puzzle_type;
const is_leaderboard_open = ref(true);

const metaStore = usePuzzleMetadataStore();
const current_variant = computed(() => metaStore.getSelectedVariant(puzzle_type));
const size = computed(() => current_variant.value[0]);
const difficulty = computed(() => current_variant.value[1]);

const leaderStore = usePuzzleLeaderboardStore();
watch(
  () => metaStore.getSelectedVariant(puzzle_type),
  async (newVariant) => {
    await leaderStore.refreshLeaderboard(puzzle_type, newVariant[0], newVariant[1]);
  },
  { immediate: true },
);

// Compute whether to show overlay/blur and what message to show
const is_ineligible = computed(() => {
  // If tutorial was used on this puzzle, always ineligible
  if (puzzle.tutorial_used_on_current_puzzle.value) return true;
  // If tutorial mode is currently on (but hasn't been used yet), also ineligible
  if (puzzle.state_ui.value.tutorial_mode) return true;
  return false;
});

const tutorial_message = computed(() => {
  const tutorial_on = puzzle.state_ui.value.tutorial_mode;
  const tutorial_used = puzzle.tutorial_used_on_current_puzzle.value;

  if (tutorial_on && tutorial_used) {
    return {
      title: "Tutorial Mode Active",
      description: "You've received tutorial feedback on this puzzle. You will be eligible for the leaderboard on the next puzzle.",
    };
  } else if (tutorial_on && !tutorial_used) {
    return {
      title: "Tutorial Mode Active",
      description: "You cannot enter the leaderboard while tutorial mode is enabled. Turn off tutorial mode to remain eligible, or continue using tutorial to receive feedback.",
    };
  } else if (!tutorial_on && tutorial_used) {
    return {
      title: "Tutorial Used",
      description: "You used tutorial mode on this puzzle. You will be eligible for the leaderboard on the next puzzle.",
    };
  }

  return null;
});
</script>

<template>
  <Container class="flex flex-col !bg-floralwhite">
    <div class="flex items-center justify-between cursor-pointer select-none w-full">
      <div class="flex items-center">
        <v-icon name="ri-trophy-line" :scale="1.5" class="mr-2" />
        <span class="text-xl">Leaderboard</span>
      </div>
      <v-icon
        name="md-keyboardarrowdown-round"
        :scale="1.5"
        :class="{ 'rotate-180': is_leaderboard_open }"
        @click="is_leaderboard_open = !is_leaderboard_open"
      />
    </div>
    <template v-if="is_leaderboard_open">
      <Separator class="my-2" />

      <!-- Leaderboard content (blurred when ineligible) -->
      <div v-if="!is_ineligible">
        <div
          v-if="leaderStore.getLeaderboard(puzzle_type, size, difficulty).length === 0"
          class="text-center text-gray-500 p-4"
        >
          No entries yet for the {{ size }} {{ puzzle_type }} with difficulty {{ difficulty }}.
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
      </div>

      <!-- Ineligibility message overlay (shown when tutorial used or active) -->
      <div
        v-else
        class="text-center p-4"
      >
        <div class="text-lg font-semibold text-gray-900 mb-2">{{ tutorial_message.title }}</div>
        <div class="text-sm">
          {{ tutorial_message.description }}
        </div>
      </div>
    </template>
  </Container>
</template>

<style scoped></style>
