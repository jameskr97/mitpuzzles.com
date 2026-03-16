<script setup lang="ts">
import DailyGameLayout from "./DailyGameLayout.vue";
import TentsCanvas from "@/features/games/tents/TentsCanvas.vue";
import { useDailyGame } from "./composables/useDailyGame.ts";
import { useTentsGame, TentsCell } from "@/features/games/tents/useTentsGame";
import { useCellDragHandlers } from "@/core/games/composables";
import type { TentsMeta } from "@/core/games/types/puzzle-types";

const daily = await useDailyGame<ReturnType<typeof useTentsGame>, TentsMeta>({
  puzzle_type: "tents",
  create_game: useTentsGame,
});

const { on_cell_click, on_cell_drag } = useCellDragHandlers(daily.game, daily.recorder);

function on_gutter_click(is_row: boolean, index: number, _button: number) {
  const result = daily.game.value.handle_line_toggle!(is_row, index, TentsCell.EMPTY, TentsCell.GREEN);
  if (result.changes.length > 0) {
    for (const change of result.changes) {
      daily.recorder.record_click({ row: change.row, col: change.col }, change.old_value, change.new_value);
    }
    daily.recorder.save_board_state(daily.game.value.board.value);
  }
}
</script>

<template>
  <DailyGameLayout :controller="daily.controller" :definition="daily.controller.state.value.definition" :date="daily.date" :error="daily.error">
    <TentsCanvas
      :key="daily.canvas_key.value"
      :state="daily.puzzle_state.value as any"
      @cell-click="on_cell_click"
      @cell-drag="on_cell_drag"
      @cell-enter="daily.on_cell_enter"
      @cell-leave="daily.on_cell_leave"
      @gutter-click="on_gutter_click"
    />
  </DailyGameLayout>
</template>
