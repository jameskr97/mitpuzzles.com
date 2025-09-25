<!-- GameView.vue - Main layout component with provide/inject -->
<script setup lang="ts">
import { type PropType, provide } from "vue";
import { useRoute } from "vue-router";
import { useGameLayout } from "@/composables/useGameLayout";

// Components
import Container from "@/components/ui/Container.vue";
import { Badge } from "@/components/ui/badge";
import { getPuzzleDisplayName } from "@/utils";
import type { PUZZLE_TYPES } from "@/constants.ts";
import FreeplayGameViewControlbar from "@/features/freeplay/FreeplayGameViewControlbar.vue";
import FreeplayGameViewViolations from "@/features/freeplay/FreeplayGameViewViolations.vue";
import FreeplayGameViewLeaderboard from "@/features/freeplay/FreeplayGameViewLeaderboard.vue";
import type { PuzzleController } from "@/services/game/engines/types.ts";
import { usePuzzleMetadataStore } from "@/store/puzzle/usePuzzleMetadataStore.ts";
import { usePuzzleScaleStore } from "@/store/puzzle/usePuzzleScaleStore.ts";

const props = defineProps({
  puzzle: { type: Object as PropType<PuzzleController>, required: true },
});

// Initialize shared state once
const route = useRoute();
const gt = route.meta.game_type as PUZZLE_TYPES;

const layout = useGameLayout();
const scaleStore = usePuzzleScaleStore();
const metaStore = usePuzzleMetadataStore();
const scale_remapped = scaleStore.getScaleRemapped(gt);

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
    <Container class="mt-2 w-full md:max-w-prose mx-auto h-12">
      <div class="m-0 p-0 grid grid-cols-3 text-xl">
        <Badge variant="default" v-if="puzzle.state_ui.value.tutorial_mode" class="justify-self-start text-nowrap">
          Tutorial Mode
        </Badge>
        <span class="col-start-2 text-center items-center">
          {{ getPuzzleDisplayName(metaStore.getSelectedVariant(puzzle.state_puzzle.value.definition.puzzle_type)) }}
        </span>
        <Badge
          v-if="puzzle.state_ui.value.show_solved_state"
          :variant="puzzle.state_puzzle.value.solved ? 'blue' : 'destructive'"
          class="justify-self-end text-nowrap text-base"
        >
          <span v-if="puzzle.state_puzzle.value.solved">You got it!</span>
          <span v-else>Not Quite!</span>
        </Badge>
      </div>
    </Container>

    <!-- Main game area -->
    <div class="grid grid-cols-2 gap-2">
      <!-- Game board slot -->
      <div class="grid md:grid-cols-[auto_1fr_auto] mx-auto col-span-full m-2 gap-2 justify-self-center">
        <slot v-if="$slots['game-left']" name="game-left"></slot>
        <div class="order-first md:order-none select-none origin-center transform-gpu" :class="{ 'pointer-events-none': puzzle.state_puzzle.value.solved === true }">
          <Container :class="{ 'shake-once': puzzle.state_ui.value.animate_failure, 'heartbeat-once': puzzle.state_ui.value.animate_success }">
            <slot name="default" :scale="scale_remapped"></slot>
          </Container>
        </div>
        <slot v-if="$slots['game-right']" name="game-right" class=""></slot>
      </div>

      <!-- Side panels -->
      <div class="flex flex-col mx-auto gap-2 col-span-2">
        <FreeplayGameViewViolations
          v-if="puzzle.state_ui.value.tutorial_mode"
          :violations="puzzle.state_puzzle.value.violations"
        />
        <FreeplayGameViewLeaderboard v-if="layout.leaderboard_visible.value" />
      </div>
    </div>
  </div>
</template>
