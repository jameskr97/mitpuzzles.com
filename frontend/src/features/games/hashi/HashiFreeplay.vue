<script setup lang="ts">
/**
 * HashiFreeplay - freeplay/daily mode wrapper for hashi (bridges).
 *
 * uses useGameSession via inject-based mode switching.
 * bridge-based interaction (different from cell-based games).
 */
import { inject } from "vue";
import { useHashiGame, type HashiGameReturn } from "./useHashiGame";
import { useFreeplayServices } from "@/features/freeplay/composables";
import { useDailyServices } from "@/features/daily/composables/useDailyServices";
import { useGameSession } from "@/core/games/composables";
import GameLayout from "@/features/freeplay/GameLayout.vue";
import HashiCanvas from "./HashiCanvas.vue";
import type { HashiMeta, HashiBridge } from "@/core/games/types/puzzle-types.ts";

const puzzle_type = "hashi";
const mode = inject<string | null>("puzzle-type-override", null);

// convert saved board format [r1, c1, r2, c2, count][] back to HashiBridge[]
function parse_saved_bridges(saved: number[][] | null): HashiBridge[] {
  if (!saved || saved.length === 0) return [];
  return saved.map((b) => ({
    island1: [b[0], b[1]] as [number, number],
    island2: [b[2], b[3]] as [number, number],
    count: b[4],
  }));
}

// serialize bridges to number[][] for persistence
function serialize_bridges(game: HashiGameReturn): number[][] {
  return game.bridges.value.map((b: HashiBridge) => [
    b.island1[0], b.island1[1],
    b.island2[0], b.island2[1],
    b.count,
  ]);
}

const services = mode === "daily"
  ? useDailyServices<HashiMeta>()
  : await useFreeplayServices<HashiMeta>(puzzle_type, { starting_state: [] });

const session = useGameSession({
  puzzle_type: mode === "daily" ? "daily" : puzzle_type,
  services,
  create_game: (def, saved_state) => useHashiGame(def, parse_saved_bridges(saved_state)),
  get_saveable_state: serialize_bridges,
  get_puzzle_state: (game, solved) => ({
    definition: game.definition,
    bridges: game.bridges.value,
    islands: game.islands.value,
    island_bridge_counts: game.island_bridge_counts.value,
    tutorial_mode: session.controller.ui.value.tutorial_mode,
    solved,
  }),
});

// handle bridge toggle
function on_bridge_toggle(island1: [number, number], island2: [number, number], button: number) {
  const result = session.game.value.toggle_bridge(island1, island2, button);
  if (result) {
    session.recorder.record_click(
      { row: island1[0], col: island1[1] },
      result.old_count,
      result.new_count
    );
    session.recorder.save_board_state(serialize_bridges(session.game.value) as any);
  }
}
</script>

<template>
  <GameLayout :controller="session.controller" :definition="session.controller.state.value.definition">
    <HashiCanvas
      :key="session.canvas_key.value"
      :state="session.puzzle_state.value"
      @bridge-toggle="on_bridge_toggle"
    />
  </GameLayout>
</template>
