<script setup lang="ts">
/** SudokuFreeplay - Freeplay mode wrapper for Sudoku */
import { computed, ref, watch, shallowRef } from "vue";
import { useSudokuGame, type SudokuGameReturn } from "./useSudokuGame";
import { useFreeplayServices } from "@/composables/freeplay";
import { useDataRecorder } from "@/composables/game-primitives";
import type { GameController, GameUIState } from "@/types/game-controller";
import GameLayout from "@/features/freeplay/GameLayout.vue";
import SudokuCanvas from "./SudokuCanvas.vue";
import SudokuNumberPad from "@/features/games/sudoku/SudokuNumberPad.vue";
import Container from "@/components/ui/Container.vue";

const puzzle_type = "sudoku";
const services = await useFreeplayServices(puzzle_type);

const last_selected_cell = ref<{ row: number; col: number } | null>(null);
const game = shallowRef<SudokuGameReturn>(
  useSudokuGame(services.definition.value, services.saved_board.value)
);

const recorder = useDataRecorder({ mode: "freeplay", puzzle_type, persist: true, broadcast: true });

const ui = ref<GameUIState>({
  show_solved_state: services.is_solved.value,
  tutorial_mode: false,
  animate_success: false,
  animate_failure: false,
});

const violations = computed(() => (ui.value.tutorial_mode ? game.value.get_violations() : []));

watch(() => ui.value.tutorial_mode, (is_on) => {
  if (is_on && violations.value.length > 0) services.mark_tutorial_used();
});

function on_cell_click(row: number, col: number) {
  last_selected_cell.value = { row, col };
}

function on_cell_key(row: number, col: number, key: string) {
  const result = game.value.handle_key_input(row, col, key);
  if (result) {
    recorder.record_click({ row, col }, result.old_value, result.new_value);
    recorder.save_board_state(game.value.board.value);
  }
}

function on_numpad_key(key: string) {
  if (!last_selected_cell.value) return;
  on_cell_key(last_selected_cell.value.row, last_selected_cell.value.col, key);
}

async function check_solution(): Promise<boolean> {
  const is_correct = await game.value.check_solution();
  ui.value.show_solved_state = true;
  ui.value.animate_success = is_correct;
  ui.value.animate_failure = !is_correct;
  if (is_correct) await services.mark_solved();
  else setTimeout(() => { ui.value.show_solved_state = false; }, 3000);
  setTimeout(() => { ui.value.animate_success = false; ui.value.animate_failure = false; }, 100);
  recorder.record_attempt_solve(is_correct);
  return is_correct;
}

function clear_puzzle() {
  const old_board = JSON.parse(JSON.stringify(game.value.board.value));
  game.value.clear();
  const new_board = JSON.parse(JSON.stringify(game.value.board.value));
  recorder.record_clear(old_board, new_board);
  recorder.save_board_state(new_board);
  ui.value.show_solved_state = false;
}

async function request_new_puzzle() {
  const new_def = await services.request_new_puzzle();
  game.value = useSudokuGame(new_def, null);
  ui.value.show_solved_state = false;
  ui.value.tutorial_mode = false;
}

const controller: GameController = {
  puzzle_type,
  state: computed(() => ({
    solved: services.is_solved.value,
    definition: {
      id: game.value.definition.id,
      puzzle_type: game.value.definition.puzzle_type,
      rows: game.value.definition.rows,
      cols: game.value.definition.cols,
    },
  })),
  ui,
  current_variant: services.current_variant,
  tutorial_used: services.tutorial_used,
  check_solution,
  clear_puzzle,
  request_new_puzzle,
};

const puzzle_state = computed(() => ({
  definition: game.value.definition,
  board: game.value.board.value,
  solved: services.is_solved.value,
  immutable_cells: game.value.immutable_cells.value,
  violations: violations.value,
}));

const canvas_key = computed(() => `${game.value.definition.id}-${game.value.definition.rows}-${game.value.definition.cols}`);
</script>

<template>
  <GameLayout :controller="controller" :definition="controller.state.value.definition">
    <SudokuCanvas
      :key="canvas_key"
      :state="puzzle_state"
      :is_prefilled="game.is_prefilled"
      :box_size="game.box_size.value"
      @cell-click="on_cell_click"
      @cell-key="on_cell_key"
    />

    <template #controls>
      <Container class="max-w-fit mx-auto">
        <SudokuNumberPad :state="puzzle_state" @key-press="on_numpad_key" />
      </Container>
    </template>
  </GameLayout>
</template>
