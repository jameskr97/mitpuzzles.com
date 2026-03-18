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
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/core/components/ui/select";
import { usePuzzleLeaderboardStore } from "@/core/store/puzzle/usePuzzleLeaderboardStore";
import { useDailyPuzzleStore } from "@/core/store/puzzle/useDailyPuzzleStore";
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
const daily_store = useDailyPuzzleStore();

// Refresh leaderboard when variant, time period, or mode changes
watch(
  () => [props.current_variant, time_period.value, scoring_method.value, controller.is_daily.value, controller.daily_date.value] as const,
  async ([variant, period, method, is_daily, daily_date]) => {
    if (is_daily && daily_date) {
      await daily_store.refreshDailyLeaderboard(daily_date, props.puzzle_type);
    } else if (variant[0] && variant[1]) {
      await leaderboard_store.refreshLeaderboard(props.puzzle_type, variant[0], variant[1], period, method);
    }
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
const leaderboard_entries = computed(() => {
  if (controller.is_daily.value && controller.daily_date.value) {
    return daily_store.getDailyLeaderboard(controller.daily_date.value, props.puzzle_type);
  }
  return leaderboard_store.getLeaderboard(props.puzzle_type, size.value, difficulty.value, time_period.value, scoring_method.value);
});
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
      <div class="flex items-center gap-2">
        <Select v-if="!controller.is_daily.value" v-model="scoring_method">
          <SelectTrigger class="h-8 w-24 text-sm">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="ao_n">{{ $t('freeplay:leaderboard.scoring_ao3') }}</SelectItem>
            <SelectItem value="best">{{ $t('freeplay:leaderboard.scoring_best') }}</SelectItem>
          </SelectContent>
        </Select>
        <v-icon
          name="md-keyboardarrowdown-round"
          :scale="1.5"
          :class="{ 'rotate-180': is_leaderboard_open }"
          @click="is_leaderboard_open = !is_leaderboard_open"
        />
      </div>
    </div>

    <template v-if="is_leaderboard_open">
      <Separator class="mt-2 mb-1" />

      <!-- Time period selector (hidden in daily mode) -->
      <div v-if="!controller.is_daily.value" class="flex justify-between">
        <Button
          class="px-3"
          v-for="period in [
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
