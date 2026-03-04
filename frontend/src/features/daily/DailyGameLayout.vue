<script setup lang="ts">
/**
 * DailyGameLayout - Simplified layout for daily challenge games.
 * No difficulty selector, no "New Puzzle" button.
 * Shows daily leaderboard instead of freeplay leaderboard.
 */
import { computed, provide } from "vue";
import type { GameController, GameDefinition } from "@/core/games/types/game-controller";
import Container from "@/core/components/ui/Container.vue";
import { usePuzzleScaleStore } from "@/core/store/puzzle/usePuzzleScaleStore";
import { ACTIVE_GAMES } from "@/constants";
import { useGameLayout } from "@/core/composables/useGameLayout";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/core/components/ui/dialog";
import GameLayoutStatusbar from "@/features/freeplay/GameLayoutStatusbar.vue";
import GameLayoutInstructions from "@/features/freeplay/GameLayoutInstructions.vue";
import DailyControlbar from "./DailyControlbar.vue";
import DailyLeaderboard from "./DailyLeaderboard.vue";

const props = defineProps<{
  controller: GameController;
  definition: GameDefinition;
  date: string;
  error?: string | null;
}>();

const scale_store = usePuzzleScaleStore();
const puzzle_type = props.controller.puzzle_type;
const layout = useGameLayout();
const game_entry = ACTIVE_GAMES[puzzle_type];
const game_title = computed(() => puzzle_type.charAt(0).toUpperCase() + puzzle_type.slice(1));

provide("game-controller", props.controller);

const container_width = computed(() => {
  const is_mobile = typeof window !== "undefined" && window.innerWidth < 768;
  if (is_mobile) return undefined;
  const BASE_WIDTH = 400;
  const scale = scale_store.getScaleRemapped(puzzle_type);
  return Math.floor(BASE_WIDTH * scale);
});
</script>

<template>
  <Dialog v-model:open="layout.instructions_visible.value">
    <DialogContent>
      <DialogHeader>
        <DialogTitle class="text-2xl">{{ game_title }} Instructions</DialogTitle>
      </DialogHeader>
      <component v-if="game_entry?.instructions" :is="game_entry.instructions" />
    </DialogContent>
  </Dialog>

  <div class="flex flex-col md:flex-row md:justify-center gap-2 w-full">
    <div class="flex flex-col gap-2 h-full min-w-0">
      <DailyControlbar :controller="controller" :date="date" class="lg:min-w-[65ch]" />
      <GameLayoutStatusbar v-if="!error" :controller="controller" />

      <Container v-if="error" class="w-full max-w-full mx-auto py-12">
        <div class="text-center">
          <h2 class="text-xl font-semibold text-gray-700 mb-2">No Puzzles Available</h2>
          <p class="text-gray-500">{{ error }}</p>
        </div>
      </Container>

      <Container
        v-else
        class="w-full max-w-full mx-auto"
        :style="container_width ? { width: container_width + 'px' } : {}"
        :class="{
          'shake-once': controller.ui.value.animate_failure,
          'heartbeat-once': controller.ui.value.animate_success,
          'pointer-events-none': controller.state.value.solved === true,
        }"
      >
        <slot />
      </Container>

      <slot name="controls" />
    </div>

    <div class="flex flex-col gap-2 w-full md:w-auto h-full md:ml-2 md:mt-39">
      <GameLayoutInstructions
        :puzzle_type="puzzle_type"
        :definition="definition"
        class="w-full md:w-80 flex-shrink"
      />
      <DailyLeaderboard
        :puzzle_type="puzzle_type"
        :date="date"
        class="w-full md:w-80 flex-shrink"
      />
    </div>
  </div>
</template>
