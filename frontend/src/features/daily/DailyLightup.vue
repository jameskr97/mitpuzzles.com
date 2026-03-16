<script setup lang="ts">
import DailyGameLayout from "./DailyGameLayout.vue";
import LightupCanvas from "@/features/games/lightup/LightupCanvas.vue";
import { useDailyGame } from "./composables/useDailyGame.ts";
import { useLightupGame } from "@/features/games/lightup/useLightupGame";
import { useCellDragHandlers } from "@/core/games/composables";

const daily = await useDailyGame({
  puzzle_type: "lightup",
  create_game: useLightupGame,
  extra_puzzle_state: (game) => ({ lit_cells: game.lit_cells.value }),
});

const { on_cell_click, on_cell_drag } = useCellDragHandlers(daily.game, daily.recorder);
</script>

<template>
  <DailyGameLayout :controller="daily.controller" :definition="daily.controller.state.value.definition" :date="daily.date" :error="daily.error">
    <LightupCanvas
      :key="daily.canvas_key.value"
      :state="daily.puzzle_state.value as any"
      @cell-click="on_cell_click"
      @cell-drag="on_cell_drag"
      @cell-enter="daily.on_cell_enter"
      @cell-leave="daily.on_cell_leave"
    />
  </DailyGameLayout>
</template>
