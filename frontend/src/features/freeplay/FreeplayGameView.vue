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
import { useGameScalesStore, usePuzzleMetadataStore } from "@/store/game.ts";
import type { PuzzleController } from "@/services/game/engines/types.ts";

const props = defineProps({
  puzzle: { type: Object as PropType<PuzzleController>, required: true },
});

// Initialize shared state once
const route = useRoute();
const gt = route.meta.game_type as PUZZLE_TYPES;

const layout = useGameLayout();
const scaleStore = useGameScalesStore();
const metaStore = usePuzzleMetadataStore();
const scale_remapped = scaleStore.getScaleRemapped(gt);

// Provide to all child components
provide("puzzle", props.puzzle);
provide("layout", layout);
</script>

<template>
  <div class="flex flex-col mx-auto">
    <!-- Control bar with all buttons and settings -->
    <FreeplayGameViewControlbar />

    <!-- Game header with tutorial mode indicator and puzzle name -->
    <Container class="mt-2 min-w-[65ch] max-w-[65ch] mx-auto h-12">
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
          <span v-if="puzzle.state_puzzle.value.solved">Your solution is correct</span>
          <span v-else>Not Quite!</span>
        </Badge>
      </div>
    </Container>

    <!-- Main game area -->
    <div class="grid grid-cols-2 gap-2">
      <!-- Game board slot -->
      <div class="mx-auto col-span-full m-2 justify-self-center flex justify-center items-center">
        <div
          class="select-none origin-center transform-gpu"
          :class="{ 'pointer-events-none': puzzle.state_puzzle.value.solved === true }"
        >
          <Container>
            <slot name="default" :scale="scale_remapped"></slot>
          </Container>
        </div>
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
