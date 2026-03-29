<script setup lang="ts">
import GameLayout from "@/features/freeplay/GameLayout.vue";
import AquariumCanvas from "./AquariumCanvas.vue";
import { useAquariumGame, AquariumCell, type AquariumMeta } from "./useAquariumGame";
import { useCellDragHandlers, useGameForMode } from "@/core/games/composables";

const freeplay = await useGameForMode<ReturnType<typeof useAquariumGame>, AquariumMeta>({
  puzzle_type: "aquarium",
  create_game: useAquariumGame,
});

const { on_cell_click, on_cell_drag } = useCellDragHandlers(freeplay.game, freeplay.recorder);

function on_gutter_click(is_row: boolean, index: number, _button: number) {
  const result = freeplay.game.value.handle_line_toggle!(is_row, index, AquariumCell.EMPTY, AquariumCell.CROSS);
  if (result.changes.length > 0) {
    for (const change of result.changes) {
      freeplay.recorder.record_click({ row: change.row, col: change.col }, change.old_value, change.new_value);
    }
    freeplay.recorder.save_board_state(freeplay.game.value.board.value);
  }
}
</script>

<template>
  <GameLayout :controller="freeplay.controller" :definition="freeplay.controller.state.value.definition">
    <AquariumCanvas
      :key="freeplay.canvas_key.value"
      :state="freeplay.puzzle_state.value as any"
      :get_region="freeplay.game.value.get_region"
      :same_region="freeplay.game.value.same_region"
      @cell-click="on_cell_click"
      @cell-drag="on_cell_drag"
      @cell-enter="freeplay.on_cell_enter"
      @cell-leave="freeplay.on_cell_leave"
      @gutter-click="on_gutter_click"
    />
  </GameLayout>
</template>
