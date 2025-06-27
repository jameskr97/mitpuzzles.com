<script setup lang="ts">
import { ACTIVE_GAMES } from "@/constants.ts";
import { useRoute } from "vue-router";
import { getGameScale } from "@/store/scale.ts";
import GameViewComponent from "@/components/gameview.component.vue";
import { createPuzzleInteractionBridge } from "@/features/games.composables/setupPuzzleInteractionBridge.ts";
import { usePuzzleController } from "@/composables/usePuzzleController.ts";
import type { SupportedPuzzleTypes } from "@/codegen/websocket/game.schema";

// load game rules as markdown
const route = useRoute();
const gt = route.meta.game_type as SupportedPuzzleTypes;
const game_entry = ACTIVE_GAMES[gt];

// load game state + data
const puzzle = usePuzzleController(gt);
const bridge = createPuzzleInteractionBridge(gt);
for (const withBehavior of game_entry["defaultBehaviors"]) {
  withBehavior(puzzle, bridge);
}

const scale = getGameScale();
</script>

<template>
  <GameViewComponent>
    <div v-if="!puzzle.isReady.value">Loading...</div>
    <component
      v-else
      :is="game_entry.component"
      :state="puzzle.state.value"
      :scale="scale.scale_remapped.value"
      :interact="bridge"
    />
  </GameViewComponent>
</template>
