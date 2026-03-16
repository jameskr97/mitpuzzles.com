<script setup lang="ts">
import { ref } from "vue";
import DailyGameLayout from "./DailyGameLayout.vue";
import SudokuCanvas from "@/features/games/sudoku/SudokuCanvas.vue";
import SudokuNumberPad from "@/features/games/sudoku/SudokuNumberPad.vue";
import Container from "@/core/components/ui/Container.vue";
import { useDailyGame } from "./composables/useDailyGame.ts";
import { useSudokuGame } from "@/features/games/sudoku/useSudokuGame";

const daily = await useDailyGame({
  puzzle_type: "sudoku",
  create_game: useSudokuGame,
});

const last_selected_cell = ref<{ row: number; col: number } | null>(null);

function on_cell_click(row: number, col: number) {
  last_selected_cell.value = { row, col };
}

function on_cell_key(row: number, col: number, key: string) {
  const result = daily.game.value.handle_key_input(row, col, key);
  if (result) {
    daily.recorder.record_click({ row, col }, result.old_value, result.new_value);
    daily.recorder.save_board_state(daily.game.value.board.value);
  }
}

function on_numpad_key(key: string) {
  if (!last_selected_cell.value) return;
  on_cell_key(last_selected_cell.value.row, last_selected_cell.value.col, key);
}
</script>

<template>
  <DailyGameLayout :controller="daily.controller" :definition="daily.controller.state.value.definition" :date="daily.date" :error="daily.error">
    <SudokuCanvas
      :key="daily.canvas_key.value"
      :state="daily.puzzle_state.value as any"
      :is_prefilled="daily.game.value.is_prefilled"
      :box_size="daily.game.value.box_size.value"
      @cell-click="on_cell_click"
      @cell-key="on_cell_key"
      @cell-enter="daily.on_cell_enter"
      @cell-leave="daily.on_cell_leave"
    />

    <template #controls>
      <Container class="max-w-fit mx-auto">
        <SudokuNumberPad :state="daily.puzzle_state.value as any" @key-press="on_numpad_key" />
      </Container>
    </template>
  </DailyGameLayout>
</template>
