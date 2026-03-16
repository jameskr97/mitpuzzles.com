<script setup lang="ts">
import { ref } from "vue";
import GameLayout from "@/features/freeplay/GameLayout.vue";
import SudokuCanvas from "./SudokuCanvas.vue";
import SudokuNumberPad from "./SudokuNumberPad.vue";
import Container from "@/core/components/ui/Container.vue";
import { useFreeplayGame } from "@/features/freeplay/composables/useFreeplayGame.ts";
import { useSudokuGame } from "./useSudokuGame";

const freeplay = await useFreeplayGame({
  puzzle_type: "sudoku",
  create_game: useSudokuGame,
});

const last_selected_cell = ref<{ row: number; col: number } | null>(null);

function on_cell_click(row: number, col: number) {
  last_selected_cell.value = { row, col };
}

function on_cell_key(row: number, col: number, key: string) {
  const result = freeplay.game.value.handle_key_input(row, col, key);
  if (result) {
    freeplay.recorder.record_click({ row, col }, result.old_value, result.new_value);
    freeplay.recorder.save_board_state(freeplay.game.value.board.value);
  }
}

function on_numpad_key(key: string) {
  if (!last_selected_cell.value) return;
  on_cell_key(last_selected_cell.value.row, last_selected_cell.value.col, key);
}
</script>

<template>
  <GameLayout :controller="freeplay.controller" :definition="freeplay.controller.state.value.definition">
    <SudokuCanvas
      :key="freeplay.canvas_key.value"
      :state="freeplay.puzzle_state.value as any"
      :is_prefilled="freeplay.game.value.is_prefilled"
      :box_size="freeplay.game.value.box_size.value"
      @cell-click="on_cell_click"
      @cell-key="on_cell_key"
      @cell-enter="freeplay.on_cell_enter"
      @cell-leave="freeplay.on_cell_leave"
    />

    <template #controls>
      <Container class="max-w-fit mx-auto">
        <SudokuNumberPad :state="freeplay.puzzle_state.value as any" @key-press="on_numpad_key" />
      </Container>
    </template>
  </GameLayout>
</template>
