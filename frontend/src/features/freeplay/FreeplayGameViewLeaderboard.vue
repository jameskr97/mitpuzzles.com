<script setup lang="ts">
import { inject, watch, computed, ref } from "vue";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/core/components/ui/table";
import Container from "@/core/components/ui/Container.vue";
import type { PuzzleController } from "@/core/games/types/puzzle-types.ts";
import { usePuzzleMetadataStore } from "@/core/store/puzzle/usePuzzleMetadataStore.ts";
import { usePuzzleLeaderboardStore } from "@/core/store/puzzle/usePuzzleLeaderboardStore.ts";
import { Separator } from "@/core/components/ui/separator";
import { Button } from "@/core/components/ui/button";
import { useTranslation } from "i18next-vue";

const { t } = useTranslation();

const props = defineProps<{
  puzzle?: PuzzleController
}>();

const puzzle = inject<PuzzleController>("puzzle") || props.puzzle!;
const puzzle_type = puzzle.state_puzzle.value.definition.puzzle_type;
const is_leaderboard_open = ref(true);
const time_period = ref<string>("weekly");

const metaStore = usePuzzleMetadataStore();
const current_variant = computed(() => metaStore.getSelectedVariant(puzzle_type));
const size = computed(() => current_variant.value[0]);
const difficulty = computed(() => current_variant.value[1]);

const leaderStore = usePuzzleLeaderboardStore();
watch(
  () => [metaStore.getSelectedVariant(puzzle_type), time_period.value] as const,
  async ([newVariant, newTimePeriod]) => {
    await leaderStore.refreshLeaderboard(puzzle_type, newVariant[0], newVariant[1], newTimePeriod);
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
      title: t('freeplay:leaderboard.tutorial_active_title'),
      description: t('freeplay:leaderboard.tutorial_active_used_desc'),
    };
  } else if (tutorial_on && !tutorial_used) {
    return {
      title: t('freeplay:leaderboard.tutorial_active_title'),
      description: t('freeplay:leaderboard.tutorial_active_unused_desc'),
    };
  } else if (!tutorial_on && tutorial_used) {
    return {
      title: t('freeplay:leaderboard.tutorial_used_title'),
      description: t('freeplay:leaderboard.tutorial_used_desc'),
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
        <span class="text-xl">{{ $t('freeplay:leaderboard.title') }}</span>
      </div>
      <v-icon
        name="md-keyboardarrowdown-round"
        :scale="1.5"
        :class="{ 'rotate-180': is_leaderboard_open }"
        @click="is_leaderboard_open = !is_leaderboard_open"
      />
    </div>
    <template v-if="is_leaderboard_open">
      <Separator class="mt-2 mb-1" />

      <!-- Time period selector -->
      <div class="flex justify-between">
        <Button
          class="px-3"
          v-for="period in [
            { value: 'today', label: $t('ui:time_period.today') },
            { value: 'weekly', label: $t('ui:time_period.weekly') },
            { value: 'monthly', label: $t('ui:time_period.monthly') },
            { value: 'all_time', label: $t('ui:time_period.all_time') },
          ]"
          :key="period.value"
          :variant="time_period === period.value ? 'outline' : 'link'"
          @click="time_period = period.value"
        >
          {{ period.label }}
        </Button>
      </div>

      <!-- Leaderboard content (blurred when ineligible) -->
      <div v-if="!is_ineligible">
        <div
          v-if="leaderStore.getLeaderboard(puzzle_type, size, difficulty, time_period).length === 0"
          class="text-center text-gray-500 p-4"
        >
          {{ $t('freeplay:leaderboard.no_entries', { size, puzzle_type, difficulty }) }}
        </div>
        <Table v-else>
          <TableHeader>
            <TableRow>
              <TableHead class="p-0">{{ $t('ui:table.rank') }}</TableHead>
              <TableHead>{{ $t('ui:table.time') }}</TableHead>
              <TableHead>{{ $t('ui:table.username') }}</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow
              v-for="(entry, index) in leaderStore.getLeaderboard(puzzle_type, size, difficulty, time_period)"
              :class="{ 'font-bold': entry.is_current_user }"
              :key="index"
            >
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
