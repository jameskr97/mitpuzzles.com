<script setup lang="ts">
import { computed } from "vue";
import { useFreeplayPuzzle } from "@/composables/useFreeplayPuzzle.ts";
import { ACTIVE_GAMES } from "@/constants.ts";
import FreeplayGameViewLeaderboard from "@/features/freeplay/FreeplayGameViewLeaderboard.vue";
import CompactInstructions from "@/features/freeplay/CompactInstructions.vue";
import Container from "@/components/ui/Container.vue";
import FreeplayGameViewControlbar from "@/features/freeplay/FreeplayGameViewControlbar.vue";
import { createPuzzleInteractionBridge } from "@/features/games.composables/setupPuzzleInteractionBridge.ts";
import { usePuzzleScaleStore } from "@/store/puzzle/usePuzzleScaleStore.ts";
import FreeplayStatusBar from "@/features/freeplay/FreeplayStatusBar.vue";
import SudokuNumberPad from "@/features/games/sudoku/SudokuNumberPad.vue";
import { useRoute } from "vue-router";

const route = useRoute();
const gt = route.meta.game_type as string;
const puzzle = await useFreeplayPuzzle(gt);
const game_entry = ACTIVE_GAMES[gt];
const scale_store = usePuzzleScaleStore();

// Create interaction bridge
const bridge = createPuzzleInteractionBridge(puzzle, false);
if (bridge) {
  // Apply game-specific behaviors if defined (e.g., nonogram gutter marking)
  if (game_entry.defaultBehaviors && game_entry.defaultBehaviors.length > 0) {
    game_entry.defaultBehaviors.forEach((behavior: any) => behavior(puzzle, bridge));
  } else {
    // Otherwise use default behaviors
    bridge.addDefaultBehaviors();
  }
}

// Compute container width for desktop based on scale
const container_width = computed(() => {
  const is_mobile = typeof window !== 'undefined' && window.innerWidth < 768;
  if (is_mobile) return undefined; // Use w-full class on mobile

  // Desktop: just determine total board width
  const BASE_WIDTH = 400; // Base board width in pixels

  // Access store state directly for reactivity
  const scale_raw = scale_store.scales[gt] ?? scale_store.DEFAULT_SCALE;
  const scale = scale_store.getScaleRemapped(gt);

  return Math.floor(BASE_WIDTH * scale);
});
</script>

<template>
  <div class="flex flex-col md:flex-row md:justify-center gap-2 w-full">
    <div class="flex flex-col gap-2 h-full min-w-0">
      <FreeplayGameViewControlbar :puzzle="puzzle" class="lg:min-w-[65ch]" />
      <FreeplayStatusBar :puzzle="puzzle" />
      <Container
        class="w-full max-w-full mx-auto"
        :style="container_width ? { width: container_width + 'px' } : {}"
        :class="{
          'shake-once': puzzle.state_ui.value.animate_failure,
          'heartbeat-once': puzzle.state_ui.value.animate_success,
          'pointer-events-none': puzzle.state_puzzle.value.solved === true,
        }"
      >
        <component
          :key="puzzle.state_puzzle.value.definition.id"
          :is="game_entry.componentn"
          :state="puzzle.state_puzzle.value"
          :interact="bridge"
        />
      </Container>

      <!-- Sudoku number pad (mobile only) -->
      <Container v-if="gt === 'sudoku'" class="max-w-fit mx-auto">
        <SudokuNumberPad
        :state="puzzle.state_puzzle.value"
        :interact="bridge"
      />
      </Container>
    </div>

    <!-- Instructions -->
    <!-- to align with game board give mt-39.5 -->
    <div class="flex flex-col gap-2 w-full md:w-auto h-full">
      <CompactInstructions :puzzle="puzzle" class="w-full md:w-80 flex-shrink"/>
      <FreeplayGameViewLeaderboard :puzzle="puzzle" class="w-full md:w-80 flex-shrink" />
    </div>
  </div>
</template>

<style scoped></style>
