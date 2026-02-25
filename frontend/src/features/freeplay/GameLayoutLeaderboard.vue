<script setup lang="ts">
/**
 * GameLayoutLeaderboard - Leaderboard panel for freeplay games
 *
 * Works with the new GameController interface.
 */
import { inject, watch, computed, ref } from "vue";
import type { GameController } from "@/core/games/types/game-controller";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/core/components/ui/table";
import Container from "@/core/components/ui/Container.vue";
import { Separator } from "@/core/components/ui/separator";
import { Button } from "@/core/components/ui/button";
import { usePuzzleLeaderboardStore } from "@/core/store/puzzle/usePuzzleLeaderboardStore";
import { useTranslation } from "i18next-vue";

const { t } = useTranslation();

const props = defineProps<{
  puzzle_type: string;
  current_variant: [string, string];
}>();

// Get controller from context for tutorial state
const controller = inject<GameController>("game-controller")!;

const is_leaderboard_open = ref(true);
const scoring_method = ref<string>("ao_n");
const time_period = ref<string>("weekly");

const size = computed(() => props.current_variant[0]);
const difficulty = computed(() => props.current_variant[1]);

const leaderboard_store = usePuzzleLeaderboardStore();

// Refresh leaderboard when variant or time period changes
watch(
  () => [props.current_variant, time_period.value, scoring_method.value] as const,
  async ([variant, period, method]) => {
    await leaderboard_store.refreshLeaderboard(
      props.puzzle_type,
      variant[0],
      variant[1],
      period,
      method
    );
  },
  { immediate: true }
);

// Check if user is ineligible for leaderboard (tutorial used)
const is_ineligible = computed(() => {
  if (controller.tutorial_used.value) return true;
  if (controller.ui.value.tutorial_mode) return true;
  return false;
});

// Tutorial message based on state
const tutorial_message = computed(() => {
  const tutorial_on = controller.ui.value.tutorial_mode;
  const tutorial_used = controller.tutorial_used.value;

  if (tutorial_on && tutorial_used) {
    return {
      title: t("freeplay:leaderboard.tutorial_active_title"),
      description: t("freeplay:leaderboard.tutorial_active_used_desc"),
    };
  } else if (tutorial_on && !tutorial_used) {
    return {
      title: t("freeplay:leaderboard.tutorial_active_title"),
      description: t("freeplay:leaderboard.tutorial_active_unused_desc"),
    };
  } else if (!tutorial_on && tutorial_used) {
    return {
      title: t("freeplay:leaderboard.tutorial_used_title"),
      description: t("freeplay:leaderboard.tutorial_used_desc"),
    };
  }

  return null;
});

// Get leaderboard entries
const leaderboard_entries = computed(() =>
  leaderboard_store.getLeaderboard(
    props.puzzle_type,
    size.value,
    difficulty.value,
    time_period.value,
    scoring_method.value
  )
);
</script>

<template>
  <Container class="flex flex-col !bg-floralwhite">
    <div
      class="flex items-center justify-between cursor-pointer select-none w-full"
    >
      <div class="flex items-center">
        <v-icon name="ri-trophy-line" :scale="1.5" class="mr-2" />
        <span class="text-xl">{{ $t("freeplay:leaderboard.title") }}</span>
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

      <!-- Scoring method selector -->
      <div class="flex gap-1 justify-center">
        <Button
          class="px-3"
          v-for="method in [
            { value: 'best', label: $t('freeplay:leaderboard.scoring_best') },
            { value: 'ao_n', label: $t('freeplay:leaderboard.scoring_ao3') },
          ]"
          :key="method.value"
          :variant="scoring_method === method.value ? 'outline' : 'link'"
          @click="scoring_method = method.value"
        >
          {{ method.label }}
        </Button>
      </div>

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

      <!-- Leaderboard content -->
      <div v-if="!is_ineligible">
        <div
          v-if="leaderboard_entries.length === 0"
          class="text-center text-gray-500 p-4"
        >
          {{
            $t("freeplay:leaderboard.no_entries", {
              size,
              puzzle_type,
              difficulty,
            })
          }}
        </div>
        <Table v-else>
          <TableHeader>
            <TableRow>
              <TableHead class="p-0">{{ $t("ui:table.rank") }}</TableHead>
              <TableHead>{{ scoring_method === 'ao_n' ? $t("ui:table.avg_time") : $t("ui:table.time") }}</TableHead>
              <TableHead>{{ $t("ui:table.username") }}</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow
              v-for="(entry, index) in leaderboard_entries"
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

      <!-- Ineligibility message -->
      <div v-else class="text-center p-4">
        <div class="text-lg font-semibold text-gray-900 mb-2">
          {{ tutorial_message?.title }}
        </div>
        <div class="text-sm">
          {{ tutorial_message?.description }}
        </div>
      </div>
    </template>
  </Container>
</template>
