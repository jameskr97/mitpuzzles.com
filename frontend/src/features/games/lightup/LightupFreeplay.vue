<script setup lang="ts">
import GameLayout from "@/features/freeplay/GameLayout.vue";
import LightupCanvas from "./LightupCanvas.vue";
import { useLightupGame } from "./useLightupGame";
import { useCellDragHandlers, useGameForMode } from "@/core/games/composables";

const freeplay = await useGameForMode({
  puzzle_type: "lightup",
  create_game: useLightupGame,
  extra_puzzle_state: (game) => ({ lit_cells: game.lit_cells.value }),
});

const { on_cell_click, on_cell_drag } = useCellDragHandlers(freeplay.game, freeplay.recorder);
</script>

<template>
  <GameLayout :controller="freeplay.controller" :definition="freeplay.controller.state.value.definition">
    <LightupCanvas
      :key="freeplay.canvas_key.value"
      :state="freeplay.puzzle_state.value as any"
      @cell-click="on_cell_click"
      @cell-drag="on_cell_drag"
      @cell-enter="freeplay.on_cell_enter"
      @cell-leave="freeplay.on_cell_leave"
    />
  </GameLayout>
</template>
