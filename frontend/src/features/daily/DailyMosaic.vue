<script setup lang="ts">
import DailyGameLayout from "./DailyGameLayout.vue";
import MosaicCanvas from "@/features/games/mosaic/MosaicCanvas.vue";
import { useDailyGame } from "./composables/useDailyGame.ts";
import { useMosaicGame } from "@/features/games/mosaic/useMosaicGame";
import { useCellDragHandlers } from "@/core/games/composables";

const daily = await useDailyGame({
  puzzle_type: "mosaic",
  create_game: useMosaicGame,
});

const { on_cell_click, on_cell_drag } = useCellDragHandlers(daily.game, daily.recorder);
</script>

<template>
  <DailyGameLayout :controller="daily.controller" :definition="daily.controller.state.value.definition" :date="daily.date" :error="daily.error">
    <MosaicCanvas
      :key="daily.canvas_key.value"
      :state="daily.puzzle_state.value as any"
      :get_number_clue="daily.game.value.get_number_clue"
      @cell-click="on_cell_click"
      @cell-drag="on_cell_drag"
      @cell-enter="daily.on_cell_enter"
      @cell-leave="daily.on_cell_leave"
    />
  </DailyGameLayout>
</template>
