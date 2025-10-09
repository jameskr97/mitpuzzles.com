<!-- GameView.vue - Main layout component with provide/inject -->
<script setup lang="ts">
import { type PropType, provide, ref } from "vue";
import { useRoute } from "vue-router";
import { useGameLayout } from "@/composables/useGameLayout";

// Components
import Container from "@/components/ui/Container.vue";
import { Badge } from "@/components/ui/badge";
import { getPuzzleDisplayName } from "@/utils";
import { ACTIVE_GAMES, type PUZZLE_TYPES } from "@/constants.ts";
import FreeplayGameViewControlbar from "@/features/freeplay/FreeplayGameViewControlbar.vue";
import FreeplayGameViewViolations from "@/features/freeplay/FreeplayGameViewViolations.vue";
import FreeplayGameViewLeaderboard from "@/features/freeplay/FreeplayGameViewLeaderboard.vue";
import type { PuzzleController } from "@/services/game/engines/types.ts";
import { usePuzzleMetadataStore } from "@/store/puzzle/usePuzzleMetadataStore.ts";
import { usePuzzleScaleStore } from "@/store/puzzle/usePuzzleScaleStore.ts";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import FreeplayGameViewInstructionModal from "@/features/freeplay/FreeplayGameViewInstructionModal.vue";
import { Separator } from "@/components/ui/separator";
import CompactInstructions from "@/features/freeplay/CompactInstructions.vue";

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
    <Container class="mt-2 w-full md:max-w-prose mx-auto h-12">
      <div class="m-0 p-0 grid grid-cols-3 text-xl">
        <!-- Tutorial Mode Toggle -->
        <div class="flex items-center gap-2">
          <Switch v-model="puzzle.state_ui.value.tutorial_mode" id="tutorial-toggle" />
          <Label for="tutorial-toggle" class="cursor-pointer font-normal">Tutorial Mode</Label>
        </div>
        <span class="col-start-2 text-center items-center">
          {{ getPuzzleDisplayName(puzzle.current_puzzle_variant.value) }}
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
      <div class="col-span-full m-2">
        <!-- Left slot - fills available space on left -->
        <div v-if="$slots['game-left']" class="hidden md:flex justify-end items-start mr-5">
          <slot name="game-left"></slot>
        </div>

        <!-- Game board - always centered, never moves -->
        <div class="flex flex-col gap-2 items-center col-start-2">
          <div class="select-none origin-center transform-gpu">
            <Container
              :class="{
                'shake-once': puzzle.state_ui.value.animate_failure,
                'heartbeat-once': puzzle.state_ui.value.animate_success,
                'pointer-events-none': puzzle.state_puzzle.value.solved === true,
              }"
              class="max-w-fit mx-auto"
            >
              <slot name="default" :scale="scale_remapped" class="max-w-fit"></slot>
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
