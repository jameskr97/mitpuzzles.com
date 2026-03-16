<script setup lang="ts">
import GameLayout from "@/features/freeplay/GameLayout.vue";
import NorinoriCanvas from "./NorinoriCanvas.vue";
import { useFreeplayGame } from "@/features/freeplay/composables/useFreeplayGame.ts";
import { useNorinoriGame, type NorinoriMeta } from "./useNorinoriGame";
import { useCellDragHandlers } from "@/core/games/composables";

const freeplay = await useFreeplayGame<ReturnType<typeof useNorinoriGame>, NorinoriMeta>({
  puzzle_type: "norinori",
  create_game: useNorinoriGame,
});

const { on_cell_click, on_cell_drag } = useCellDragHandlers(freeplay.game, freeplay.recorder);
</script>

<template>
  <GameLayout :controller="freeplay.controller" :definition="freeplay.controller.state.value.definition">
    <NorinoriCanvas
      :key="freeplay.canvas_key.value"
      :state="freeplay.puzzle_state.value as any"
      :get_region="freeplay.game.value.get_region"
      :same_region="freeplay.game.value.same_region"
      @cell-click="on_cell_click"
      @cell-drag="on_cell_drag"
    />
  </GameLayout>
</template>
