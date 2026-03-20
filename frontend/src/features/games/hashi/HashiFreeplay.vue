<script setup lang="ts">
/**
 * HashiFreeplay - Freeplay mode wrapper for Hashi (Bridges)
 *
 * Uses the shared GameLayout and core game logic.
 * Bridge-based interaction (different from cell-based games).
 */
import { computed, ref, shallowRef } from "vue";
import { useHashiGame, type HashiGameReturn } from "./useHashiGame";
import { useFreeplayServices } from "@/features/freeplay/composables";
import { useDataRecorder } from "@/core/games/composables";
import type { GameController, GameUIState } from "@/core/games/types/game-controller";
import GameLayout from "@/features/freeplay/GameLayout.vue";
import HashiCanvas from "./HashiCanvas.vue";
import type { HashiMeta, HashiBridge } from "@/core/games/types/puzzle-types.ts";

const puzzle_type = "hashi";
const services = await useFreeplayServices<HashiMeta>(puzzle_type);

// Convert saved bridge format [r1, c1, r2, c2, count][] back to HashiBridge[]
function parse_saved_bridges(saved: number[][] | null): HashiBridge[] {
  if (!saved || saved.length === 0) return [];
  return saved.map((b) => ({
    island1: [b[0], b[1]] as [number, number],
    island2: [b[2], b[3]] as [number, number],
    count: b[4],
  }));
}

// Load saved bridges from progress store, or use empty array for new puzzle
const initial_bridges = parse_saved_bridges(services.saved_board.value);

if (!services.definition.value) throw new Error("no puzzle definition available");
const game = shallowRef<HashiGameReturn>(
  useHashiGame(services.definition.value, initial_bridges)
);

const recorder = useDataRecorder({
  mode: "freeplay",
  puzzle_type,
  persist: true,
  broadcast: true,
});

const ui = ref<GameUIState>({
  show_solved_state: services.is_solved.value,
  tutorial_mode: false,
  animate_success: false,
  animate_failure: false,
});

// Handle bridge toggle
function on_bridge_toggle(island1: [number, number], island2: [number, number], button: number) {
  const result = game.value.toggle_bridge(island1, island2, button);
  if (result) {
    // Record the action
    recorder.record_click(
      { row: island1[0], col: island1[1] },
      result.old_count,
      result.new_count
    );
    // Save bridge state (convert to serializable format)
    const bridges_state = game.value.bridges.value.map((b: HashiBridge) => [
      b.island1[0], b.island1[1],
      b.island2[0], b.island2[1],
      b.count,
    ]);
    recorder.save_board_state(bridges_state as any);
  }
}

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

function clear_puzzle() {
  const old_bridges = JSON.parse(JSON.stringify(game.value.bridges.value));
  game.value.clear();
  recorder.record_clear(old_bridges, []);
  recorder.save_board_state([]);
  ui.value.show_solved_state = false;
}

async function request_new_puzzle() {
  const new_def = await services.request_new_puzzle();
  if (!new_def) return;
  game.value = useHashiGame(new_def, []);
  await recorder.save_board_state([]); // reset existing bridges
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
  formatted_time: services.formatted_time,
  check_solution,
  clear_puzzle,
  request_new_puzzle,
};

// State for canvas component
const puzzle_state = computed(() => ({
  definition: game.value.definition,
  bridges: game.value.bridges.value,
  islands: game.value.islands.value,
  island_bridge_counts: game.value.island_bridge_counts.value,
}));

const canvas_key = computed(() =>
  `${game.value.definition.id}-${game.value.rows}-${game.value.cols}`
);
</script>

<template>
  <GameLayout :controller="controller" :definition="controller.state.value.definition">
    <HashiCanvas
      :key="canvas_key"
      :state="puzzle_state"
      :is_island="game.is_island"
      :find_island_in_direction="game.find_island_in_direction"
      @bridge-toggle="on_bridge_toggle"
    />
  </GameLayout>
</template>
