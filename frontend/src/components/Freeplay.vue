<script setup lang="ts">
import { ACTIVE_GAMES } from "@/constants.ts";
import { useRoute } from "vue-router";
import FreeplayGameView from "@/features/freeplay/FreeplayGameView.vue";
import { useFreeplayPuzzle } from "@/composables/useFreeplayPuzzle.ts";
import { createPuzzleInteractionBridge } from "@/features/games.composables/setupPuzzleInteractionBridge.ts";
import { useGameScalesStore } from "@/store/useGameScaleStore.ts";

const route = useRoute();
const gt = route.meta.game_type as string;
const puzzle = await useFreeplayPuzzle(gt);
const game_entry = ACTIVE_GAMES[gt];
const scaleStore = useGameScalesStore();

const bridge = createPuzzleInteractionBridge(puzzle);
for (const withBehavior of game_entry["defaultBehaviors"]) {
  withBehavior(puzzle, bridge);
}
</script>

<template>
  <FreeplayGameView :puzzle="puzzle" class="mt-2">
    <component
      :is="game_entry.component"
      :state="puzzle.state_puzzle.value"
      :scale="scaleStore.getScaleRemapped(gt)"
      :interact="bridge"
    />
  </FreeplayGameView>
</template>
