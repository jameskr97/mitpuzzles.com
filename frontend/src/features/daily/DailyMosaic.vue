<script setup lang="ts">
import { computed, ref, watch, shallowRef } from "vue";
import { useMosaicGame, type MosaicGameReturn } from "@/features/games/mosaic/useMosaicGame";
import { useDailyServices } from "./useDailyServices";
import { useDataRecorder } from "@/core/games/composables";
import type { GameController, GameUIState } from "@/core/games/types/game-controller";
import DailyGameLayout from "./DailyGameLayout.vue";
import MosaicCanvas from "@/features/games/mosaic/MosaicCanvas.vue";

const puzzle_type = "mosaic";
const services = await useDailyServices(puzzle_type);
const progress_key = `daily:${puzzle_type}`;

const game = shallowRef<MosaicGameReturn>(
  useMosaicGame(services.definition.value!, services.saved_board.value)
);
const recorder = useDataRecorder({ mode: "freeplay", puzzle_type: progress_key, persist: true, broadcast: false });

const ui = ref<GameUIState>({ show_solved_state: services.is_solved.value, tutorial_mode: false, animate_success: false, animate_failure: false });
const violations = computed(() => (ui.value.tutorial_mode ? game.value.get_violations() : []));
watch(() => ui.value.tutorial_mode, (is_on) => { if (is_on && violations.value.length > 0) services.mark_tutorial_used(); });

const drag_target_value = ref<number | null>(null);

function on_cell_click(row: number, col: number, button: number) {
  const result = game.value.handle_cell_click(row, col, button);
  if (result) { drag_target_value.value = result.new_value; recorder.record_click({ row, col }, result.old_value, result.new_value); recorder.save_board_state(game.value.board.value); }
}
function on_cell_drag(row: number, col: number) {
  if (drag_target_value.value === null) return;
  const result = game.value.set_cell_value(row, col, drag_target_value.value);
  if (result) { recorder.record_click({ row, col }, result.old_value, result.new_value); recorder.save_board_state(game.value.board.value); }
}
function on_cell_enter(row: number, col: number, zone: string) { recorder.record_hover_start({ row, col }, zone); }
function on_cell_leave(row: number, col: number, zone: string) { recorder.record_hover_end({ row, col }, zone); }

async function check_solution(): Promise<boolean> {
  const is_correct = await game.value.check_solution();
  ui.value.show_solved_state = true; ui.value.animate_success = is_correct; ui.value.animate_failure = !is_correct;
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
  recorder.record_clear(old_board, new_board); recorder.save_board_state(new_board);
  ui.value.show_solved_state = false;
}

const controller: GameController = {
  puzzle_type,
  state: computed(() => ({ solved: services.is_solved.value, definition: { id: game.value.definition.id, puzzle_type: game.value.definition.puzzle_type, rows: game.value.definition.rows, cols: game.value.definition.cols } })),
  ui, current_variant: services.current_variant, tutorial_used: services.tutorial_used,
  check_solution, clear_puzzle, request_new_puzzle: async () => {},
};

const puzzle_state = computed(() => ({ definition: game.value.definition, board: game.value.board.value, solved: services.is_solved.value, immutable_cells: game.value.immutable_cells.value, violations: violations.value }));
const canvas_key = computed(() => `${game.value.definition.id}-${game.value.definition.rows}-${game.value.definition.cols}`);
</script>

<template>
  <DailyGameLayout :controller="controller" :definition="controller.state.value.definition" :date="services.date" :error="services.error.value">
    <MosaicCanvas :key="canvas_key" :state="puzzle_state" :get_number_clue="game.get_number_clue" @cell-click="on_cell_click" @cell-drag="on_cell_drag" @cell-enter="on_cell_enter" @cell-leave="on_cell_leave" />
  </DailyGameLayout>
</template>
