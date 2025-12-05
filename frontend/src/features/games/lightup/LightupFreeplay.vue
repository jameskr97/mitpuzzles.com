<script setup lang="ts">
/**
 * LightupFreeplay - Freeplay mode wrapper for Lightup (Akari)
 *
 * Uses the shared GameLayout and core game logic.
 * Canvas-only rendering.
 */
import { computed, ref, watch, shallowRef } from "vue";
import { useLightupGame, type LightupGameReturn } from "./useLightupGame";
import { useFreeplayServices } from "@/features/freeplay/composables";
import { useDataRecorder } from "@/core/games/composables";
import type { GameController, GameUIState } from "@/core/games/types/game-controller";
import GameLayout from "@/features/freeplay/GameLayout.vue";
import LightupCanvas from "./LightupCanvas.vue";

// Initialize freeplay services
const puzzle_type = "lightup";
const services = await useFreeplayServices(puzzle_type);

// Core game logic - use shallowRef so we can swap it out for new puzzles
const game = shallowRef<LightupGameReturn>(
  useLightupGame(services.definition.value, services.saved_board.value)
);

// Data recorder for freeplay
const recorder = useDataRecorder({
  mode: "freeplay",
  puzzle_type,
  persist: true,
  broadcast: true,
});

// UI state
const ui = ref<GameUIState>({
  show_solved_state: services.is_solved.value,
  tutorial_mode: false,
  animate_success: false,
  animate_failure: false,
});

// Violations (computed when tutorial mode is on)
const violations = computed(() =>
  ui.value.tutorial_mode ? game.value.get_violations() : []
);

// Watch for tutorial mode changes to mark as used
watch(
  () => ui.value.tutorial_mode,
  (is_on) => {
    if (is_on && violations.value.length > 0) {
      services.mark_tutorial_used();
    }
  }
);

// Drag target value for click-and-drag
const drag_target_value = ref<number | null>(null);

// Handle cell click (initial click - cycles state)
function on_cell_click(row: number, col: number, button: number) {
  const result = game.value.handle_cell_click(row, col, button);
  if (result) {
    drag_target_value.value = result.new_value;
    recorder.record_click({ row, col }, result.old_value, result.new_value);
    recorder.save_board_state(game.value.board.value);
  }
}

// Handle cell drag (subsequent cells during drag - sets to target value)
function on_cell_drag(row: number, col: number) {
  if (drag_target_value.value === null) return;

  const result = game.value.set_cell_value(row, col, drag_target_value.value);
  if (result) {
    recorder.record_click({ row, col }, result.old_value, result.new_value);
    recorder.save_board_state(game.value.board.value);
  }
}

function on_cell_enter(row: number, col: number, zone: string) {
  recorder.record_hover_start({ row, col }, zone);
}

function on_cell_leave(row: number, col: number, zone: string) {
  recorder.record_hover_end({ row, col }, zone);
}

// Check solution
async function check_solution(): Promise<boolean> {
  const is_correct = await game.value.check_solution();

  ui.value.show_solved_state = true;
  ui.value.animate_success = is_correct;
  ui.value.animate_failure = !is_correct;

  if (is_correct) {
    await services.mark_solved();
  } else {
    setTimeout(() => {
      ui.value.show_solved_state = false;
    }, 3000);
  }

  setTimeout(() => {
    ui.value.animate_success = false;
    ui.value.animate_failure = false;
  }, 100);

  recorder.record_attempt_solve(is_correct);
  return is_correct;
}

// Clear puzzle
function clear_puzzle() {
  const old_board = JSON.parse(JSON.stringify(game.value.board.value));
  game.value.clear();
  const new_board = JSON.parse(JSON.stringify(game.value.board.value));
  recorder.record_clear(old_board, new_board);
  recorder.save_board_state(new_board);
  ui.value.show_solved_state = false;
}

// Request new puzzle
async function request_new_puzzle() {
  const new_def = await services.request_new_puzzle();

  // Reinitialize game with new definition
  game.value = useLightupGame(new_def, null);

  ui.value.show_solved_state = false;
  ui.value.tutorial_mode = false;
}

// Build GameController interface for GameLayout
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

// State for canvas component
const puzzle_state = computed(() => ({
  definition: game.value.definition,
  board: game.value.board.value,
  solved: services.is_solved.value,
  immutable_cells: game.value.immutable_cells.value,
  violations: violations.value,
  lit_cells: game.value.lit_cells.value,
}));

// Key for forcing canvas remount when puzzle changes
const canvas_key = computed(() =>
  `${game.value.definition.id}-${game.value.definition.rows}-${game.value.definition.cols}`
);
</script>

<template>
  <GameLayout :controller="controller" :definition="controller.state.value.definition">
    <LightupCanvas
      :key="canvas_key"
      :state="puzzle_state"
      @cell-click="on_cell_click"
      @cell-drag="on_cell_drag"
      @cell-enter="on_cell_enter"
      @cell-leave="on_cell_leave"
    />
  </GameLayout>
</template>
