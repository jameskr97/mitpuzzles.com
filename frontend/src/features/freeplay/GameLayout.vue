<script setup lang="ts">
/**
 * GameLayout - Shared layout component for freeplay games
 *
 * Consumes the GameController interface and provides the standard
 * freeplay UI (controlbar, statusbar, leaderboard, instructions).
 *
 * Games provide their own rendering via the default slot.
 */
import { computed, provide, ref } from "vue";
import { Button } from "@/core/components/ui/button";
import type { GameController, GameDefinition } from "@/core/games/types/game-controller";
import Container from "@/core/components/ui/Container.vue";
import { usePuzzleScaleStore } from "@/core/store/puzzle/usePuzzleScaleStore";
import { usePuzzleProgressStore } from "@/core/store/puzzle/usePuzzleProgressStore";
import { ACTIVE_GAMES } from "@/constants";
import { useGameLayout } from "@/core/composables/useGameLayout";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/core/components/ui/dialog";
import GameLayoutControlbar from "./GameLayoutControlbar.vue";
import GameLayoutStatusbar from "./GameLayoutStatusbar.vue";
import GameLayoutInstructions from "./GameLayoutInstructions.vue";
import GameLayoutLeaderboard from "./GameLayoutLeaderboard.vue";
import DailyLeaderboard from "@/features/daily/DailyLeaderboard.vue";

const props = defineProps<{
  controller: GameController;
  /** Full definition for instructions rendering */
  definition: GameDefinition;
  /** Error message to display (e.g., no puzzles available) */
  error?: string | null;
}>();

const scale_store = usePuzzleScaleStore();
const puzzle_type = props.definition.puzzle_type;
const is_daily = props.controller.puzzle_type === "daily";
const layout = useGameLayout();
const game_entry = ACTIVE_GAMES[puzzle_type];
const game_title = computed(() => puzzle_type.charAt(0).toUpperCase() + puzzle_type.slice(1));

// Provide controller for child components
provide("game-controller", props.controller);

// start gate — if controller has start_game and timer hasn't begun, require explicit start
const progress_store = usePuzzleProgressStore();
const already_started = !!progress_store.timestamp_start[props.controller.puzzle_type];
const game_started = ref(!props.controller.start_game || already_started);
async function handle_start() {
  if (props.controller.start_game) {
    await props.controller.start_game();
  }
  game_started.value = true;
}

// Compute container width based on scale
const container_width = computed(() => {
  const is_mobile = typeof window !== "undefined" && window.innerWidth < 768;
  if (is_mobile) return undefined;

  const BASE_WIDTH = 400;
  const scale = scale_store.getScaleRemapped(puzzle_type);
  return Math.floor(BASE_WIDTH * scale);
});
</script>

<template>
  <!-- Instructions Modal -->
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
      <!-- Control Bar -->
      <GameLayoutControlbar :controller="controller" class="lg:min-w-[65ch]" />

      <!-- Status Bar (hidden when error) -->
      <GameLayoutStatusbar v-if="!error" :controller="controller" />

      <!-- Error State -->
      <Container v-if="error" class="w-full max-w-full mx-auto py-12">
        <div class="text-center">
          <h2 class="text-xl font-semibold text-gray-700 mb-2">No Puzzles Available</h2>
          <p class="text-gray-500">{{ error }}</p>
        </div>
      </Container>

      <!-- start gate for daily -->
      <Container
        v-else-if="!game_started"
        class="w-full max-w-full mx-auto flex flex-col items-center justify-center gap-4 py-20"
        :style="container_width ? { width: container_width + 'px' } : {}"
      >
        <p class="text-gray-600 text-center">
          {{ $t("daily:start_prompt", { puzzle_type: game_title }) }}
        </p>
        <Button size="lg" @click="handle_start">
          {{ $t("ui:action.start") }}
        </Button>
      </Container>

      <!-- Game Content (provided by slot) -->
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

      <!-- Extra slot for game-specific controls (e.g., Sudoku number pad) -->
      <slot v-if="game_started" name="controls" />
    </div>

    <!-- Right sidebar: Instructions + Leaderboard -->
    <div class="flex flex-col gap-2 w-full md:w-auto h-full md:ml-2 md:mt-39">
      <GameLayoutInstructions
        :puzzle_type="puzzle_type"
        :definition="definition"
        class="w-full md:w-80 flex-shrink"
      />
      <DailyLeaderboard v-if="is_daily" class="w-full md:w-80 flex-shrink" />
      <GameLayoutLeaderboard
        v-else
        :puzzle_type="puzzle_type"
        :current_variant="controller.current_variant.value"
        class="w-full md:w-80 flex-shrink"
      />
    </div>
  </div>
</template>
