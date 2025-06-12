<script setup lang="ts">
import { ACTIVE_GAMES } from "@/main.ts";
import { useRoute } from "vue-router";
import { getGameScale } from "@/store/scale.ts";
import GameViewComponent from "@/components/gameview.component.vue";
import { useCurrentPuzzle } from "@/composables/useCurrentPuzzle.ts";
import { createPuzzleInteractionBridge } from "@/features/games.composables/setupPuzzleInteractionBridge.ts";

// load game rules as markdown
const route = useRoute();
const game_entry = ACTIVE_GAMES[route.meta.game_type as string];

// load game state + data
const puzzle = await useCurrentPuzzle();
const bridge = createPuzzleInteractionBridge(puzzle);
for(const withBehavior of game_entry["defaultBehaviors"]) {
  withBehavior(puzzle, bridge);
}

const scale = getGameScale();
</script>

<template>
  <GameViewComponent>
    <div v-if="!puzzle.is_ready">Loading...</div>
    <component
      v-if="puzzle.is_ready.value"
      :is="game_entry.component"
      :interact="bridge"
      :state="puzzle.state.value"
      :scale="scale.scale_remapped.value"
    />
  </GameViewComponent>
</template>
