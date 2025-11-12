<script setup lang="ts">
/**
 * NorinoriFreeplay - Freeplay mode wrapper for Norinori
 */
import { computed, ref, watch, shallowRef } from "vue";
import { useNorinoriGame, type NorinoriGameReturn, type NorinoriMeta } from "./useNorinoriGame";
import { useFreeplayServices } from "@/composables/freeplay";
import { useDataRecorder } from "@/composables/game-primitives";
import type { GameController, GameUIState } from "@/types/game-controller";
import GameLayout from "@/features/freeplay/GameLayout.vue";
import NorinoriCanvas from "./NorinoriCanvas.vue";

const puzzle_type = "norinori";
const services = await useFreeplayServices<NorinoriMeta>(puzzle_type);

const game = shallowRef<NorinoriGameReturn>(
  useNorinoriGame(services.definition.value, services.saved_board.value)
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

const drag_target_value = ref<number | null>(null);

function on_cell_click(row: number, col: number, button: number) {
  const result = game.value.handle_cell_click(row, col, button);
  if (result) {
    drag_target_value.value = result.new_value;
    recorder.record_click({ row, col }, result.old_value, result.new_value);
    recorder.save_board_state(game.value.board.value);
  }
}

function on_cell_drag(row: number, col: number) {
  if (drag_target_value.value === null) return;
  const result = game.value.set_cell_value(row, col, drag_target_value.value);
  if (result) {
    recorder.record_click({ row, col }, result.old_value, result.new_value);
    recorder.save_board_state(game.value.board.value);
  }
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
  game.value = useNorinoriGame(new_def, null);
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
  violations: violations.value,
}));

const canvas_key = computed(() => `${game.value.definition.id}-${game.value.definition.rows}-${game.value.definition.cols}`);
</script>

<template>
  <GameLayout :controller="controller" :definition="controller.state.value.definition">
    <NorinoriCanvas
      :key="canvas_key"
      :state="puzzle_state"
      :get_region="game.get_region"
      :same_region="game.same_region"
      @cell-click="on_cell_click"
      @cell-drag="on_cell_drag"
    />
  </GameLayout>
</template>
