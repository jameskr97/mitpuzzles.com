<!-- GameView.vue - Main layout component with provide/inject -->
<script setup lang="ts">
import { type PropType, provide, ref } from "vue";
import { useRoute } from "vue-router";
import { useGameLayout } from "@/core/composables/useGameLayout";

// Components
import Container from "@/core/components/ui/Container.vue";
import { ACTIVE_GAMES, type PUZZLE_TYPES } from "@/constants.ts";
import FreeplayGameViewControlbar from "@/features/freeplay/FreeplayGameViewControlbar.vue";
import FreeplayGameViewLeaderboard from "@/features/freeplay/FreeplayGameViewLeaderboard.vue";
import type { PuzzleController } from "@/core/games/types/puzzle-types.ts";
import { usePuzzleMetadataStore } from "@/core/store/puzzle/usePuzzleMetadataStore.ts";
import { usePuzzleScaleStore } from "@/core/store/puzzle/usePuzzleScaleStore.ts";
import CompactInstructions from "@/features/freeplay/CompactInstructions.vue";
import FreeplayStatusBar from "@/features/freeplay/FreeplayStatusBar.vue";

const props = defineProps({
  puzzle: { type: Object as PropType<PuzzleController>, required: true },
});

// Initialize shared state once
const route = useRoute();
const gt = route.meta.game_type as PUZZLE_TYPES;
const game_entry = ACTIVE_GAMES[gt];

const layout = useGameLayout();
const scaleStore = usePuzzleScaleStore();
const metaStore = usePuzzleMetadataStore();
const scale_remapped = scaleStore.getScaleRemapped(gt);
const is_game_rules_open = ref(true);

// Provide to all child components
provide("puzzle", props.puzzle);
provide("layout", layout);
</script>

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

<template>
  <div class="flex flex-col mx-auto">
    <!-- Control bar with all buttons and settings -->
    <FreeplayGameViewControlbar />

    <!-- Game header with tutorial mode indicator and puzzle name -->
    <FreeplayStatusBar />
    <!-- Main game area -->
    <div class="grid grid-cols-2 gap-2">
      <!-- Game board slot -->
      <div class="col-span-full m-2">
        <!-- Left slot - fills available space on left -->
        <div v-if="$slots['game-left']" class="hidden md:flex justify-end items-start mr-5">
          <slot name="game-left"></slot>
        </div>

        <!-- Game board - always centered, never moves -->
        <div class="flex flex-row gap-2 items-center col-start-2">
          <div class="select-none origin-center transform-gpu">
            <Container
              :class="{
                'shake-once': puzzle.state_ui.value.animate_failure,
                'heartbeat-once': puzzle.state_ui.value.animate_success,
                'pointer-events-none': puzzle.state_puzzle.value.solved === true,
              }"
              class="max-w-full mx-auto"
            >
              <slot name="default" class="max-w-fit"></slot>
            </Container>
          </div>
          <slot name="game-below"></slot>
        </div>

        <!-- Right slot - fills available space on right -->
        <div v-if="$slots['game-right']" class="hidden md:flex justify-start items-start">
          <slot name="game-right"></slot>
        </div>
      </div>

      <!-- Side panels -->
      <div class="flex flex-col md:flex-row mx-auto gap-2 col-span-2 items-start">
        <CompactInstructions :puzzle="puzzle" class="w-80 flex-shrink"/>
        <FreeplayGameViewLeaderboard class="w-80 flex-shrink" />
      </div>
    </div>
  </div>
</template>
