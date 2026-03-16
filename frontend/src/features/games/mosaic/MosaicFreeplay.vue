<script setup lang="ts">
import GameLayout from "@/features/freeplay/GameLayout.vue";
import MosaicCanvas from "./MosaicCanvas.vue";
import { useFreeplayGame } from "@/features/freeplay/composables/useFreeplayGame.ts";
import { useMosaicGame } from "./useMosaicGame";
import { useCellDragHandlers } from "@/core/games/composables";

const freeplay = await useFreeplayGame({
  puzzle_type: "mosaic",
  create_game: useMosaicGame,
});

const { on_cell_click, on_cell_drag } = useCellDragHandlers(freeplay.game, freeplay.recorder);
</script>

<template>
  <GameLayout :controller="freeplay.controller" :definition="freeplay.controller.state.value.definition">
    <MosaicCanvas
      :key="freeplay.canvas_key.value"
      :state="freeplay.puzzle_state.value as any"
      :get_number_clue="freeplay.game.value.get_number_clue"
      @cell-click="on_cell_click"
      @cell-drag="on_cell_drag"
      @cell-enter="freeplay.on_cell_enter"
      @cell-leave="freeplay.on_cell_leave"
    />
  </GameLayout>
</template>
