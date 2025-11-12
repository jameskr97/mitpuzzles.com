<script setup lang="ts">
/**
 * GameLayout - Shared layout component for freeplay games
 *
 * Consumes the GameController interface and provides the standard
 * freeplay UI (controlbar, statusbar, leaderboard, instructions).
 *
 * Games provide their own rendering via the default slot.
 */
import { computed, provide } from "vue";
import type { GameController, GameDefinition } from "@/types/game-controller";
import Container from "@/components/ui/Container.vue";
import { usePuzzleScaleStore } from "@/store/puzzle/usePuzzleScaleStore";
import { ACTIVE_GAMES } from "@/constants";
import { useGameLayout } from "@/composables/useGameLayout";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import GameLayoutControlbar from "./GameLayoutControlbar.vue";
import GameLayoutStatusbar from "./GameLayoutStatusbar.vue";
import GameLayoutInstructions from "./GameLayoutInstructions.vue";
import GameLayoutLeaderboard from "./GameLayoutLeaderboard.vue";

const props = defineProps<{
  controller: GameController;
  /** Full definition for instructions rendering */
  definition: GameDefinition;
  /** Error message to display (e.g., no puzzles available) */
  error?: string | null;
}>();

const scale_store = usePuzzleScaleStore();
const puzzle_type = props.controller.puzzle_type;
const layout = useGameLayout();
const game_entry = ACTIVE_GAMES[puzzle_type];
const game_title = computed(() => puzzle_type.charAt(0).toUpperCase() + puzzle_type.slice(1));

// Provide controller for child components
provide("game-controller", props.controller);

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
      <slot name="controls" />
    </div>

    <!-- Right sidebar: Instructions + Leaderboard -->
    <div class="flex flex-col gap-2 w-full md:w-auto h-full md:ml-2 md:mt-39">
      <GameLayoutInstructions
        :puzzle_type="puzzle_type"
        :definition="definition"
        class="w-full md:w-80 flex-shrink"
      />
      <GameLayoutLeaderboard
        :puzzle_type="puzzle_type"
        :current_variant="controller.current_variant.value"
        class="w-full md:w-80 flex-shrink"
      />
    </div>
  </div>
</template>

<style>
.shake-once {
  animation: shake 0.15s ease-in-out 2.5;
}

@keyframes shake {
  0%,
  100% {
    transform: translateX(0);
  }
  25% {
    transform: translateX(10px);
  }
  75% {
    transform: translateX(-10px);
  }
}

.heartbeat-once {
  animation: heartbeat 1s ease-in-out 1;
}

@keyframes heartbeat {
  0% {
    transform: scale(1);
  }
  14% {
    transform: scale(1.05);
  }
  28% {
    transform: scale(1);
  }
  42% {
    transform: scale(1.05);
  }
  70% {
    transform: scale(1);
  }
}
</style>
