<script setup lang="ts">
import GameLayout from "@/features/freeplay/GameLayout.vue";
import MinesweeperCanvas from "./MinesweeperCanvas.vue";
import { useFreeplayGame } from "@/features/freeplay/composables/useFreeplayGame.ts";
import { useMinesweeperGame } from "./useMinesweeperGame";
import { useCellDragHandlers } from "@/core/games/composables";

const freeplay = await useFreeplayGame({
  puzzle_type: "minesweeper",
  create_game: useMinesweeperGame,
});

const { on_cell_click, on_cell_drag } = useCellDragHandlers(freeplay.game, freeplay.recorder);
</script>

<template>
  <GameLayout :controller="freeplay.controller" :definition="freeplay.controller.state.value.definition">
    <MinesweeperCanvas
      :key="freeplay.canvas_key.value"
      :state="freeplay.puzzle_state.value as any"
      @cell-click="on_cell_click"
      @cell-drag="on_cell_drag"
      @cell-enter="freeplay.on_cell_enter"
      @cell-leave="freeplay.on_cell_leave"
    />
  </GameLayout>
</template>
