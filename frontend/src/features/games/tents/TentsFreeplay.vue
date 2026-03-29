<script setup lang="ts">
import GameLayout from "@/features/freeplay/GameLayout.vue";
import TentsCanvas from "./TentsCanvas.vue";
import { useTentsGame, TentsCell } from "./useTentsGame";
import { useCellDragHandlers, useGameForMode } from "@/core/games/composables";
import type { TentsMeta } from "@/core/games/types/puzzle-types.ts";

const freeplay = await useGameForMode<ReturnType<typeof useTentsGame>, TentsMeta>({
  puzzle_type: "tents",
  create_game: useTentsGame,
});

const { on_cell_click, on_cell_drag } = useCellDragHandlers(freeplay.game, freeplay.recorder);

function on_gutter_click(is_row: boolean, index: number, _button: number) {
  const result = freeplay.game.value.handle_line_toggle!(is_row, index, TentsCell.EMPTY, TentsCell.GREEN);
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
    <TentsCanvas
      :key="freeplay.canvas_key.value"
      :state="freeplay.puzzle_state.value as any"
      @cell-click="on_cell_click"
      @cell-drag="on_cell_drag"
      @cell-enter="freeplay.on_cell_enter"
      @cell-leave="freeplay.on_cell_leave"
      @gutter-click="on_gutter_click"
    />
  </GameLayout>
</template>
