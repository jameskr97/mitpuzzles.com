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

// convert saved board format { bridges: [r1, c1, r2, c2, count][], exhausted?: string[] } back
function parse_saved_bridges(saved: any): HashiBridge[] {
  // support both old format (number[][]) and new format ({ bridges, exhausted })
  const arr = Array.isArray(saved) ? saved : saved?.bridges;
  if (!arr || arr.length === 0) return [];
  return arr.map((b: number[]) => ({
    island1: [b[0], b[1]] as [number, number],
    island2: [b[2], b[3]] as [number, number],
    count: b[4],
  }));
}

function parse_saved_exhausted(saved: any): string[] | null {
  if (!saved || Array.isArray(saved)) return null;
  return saved.exhausted ?? null;
}

// serialize bridges + exhausted for persistence
function serialize_state(game: HashiGameReturn): { bridges: number[][]; exhausted: string[] } {
  return {
    bridges: game.bridges.value.map((b: HashiBridge) => [
      b.island1[0], b.island1[1],
      b.island2[0], b.island2[1],
      b.count,
    ]),
    exhausted: Array.from(game.exhausted.value),
  };
}

const services = mode === "daily"
  ? useDailyServices<HashiMeta>()
  : await useFreeplayServices<HashiMeta>(puzzle_type, { starting_state: [] });

const session = useGameSession({
  puzzle_type: mode === "daily" ? "daily" : puzzle_type,
  services,
  create_game: (def, saved_state) => useHashiGame(def, parse_saved_bridges(saved_state), parse_saved_exhausted(saved_state)),
  get_saveable_state: serialize_state,
  get_puzzle_state: (game, solved) => ({
    definition: game.definition,
    bridges: game.bridges.value,
    islands: game.islands.value,
    island_bridge_counts: game.island_bridge_counts.value,
    exhausted: game.exhausted.value,
    tutorial_mode: session.controller.ui.value.tutorial_mode,
    solved,
  }),
});

// handle bridge toggle (left-click)
function on_bridge_toggle(island1: [number, number], island2: [number, number]) {
  const result = session.game.value.toggle_bridge(island1, island2);
  if (result) {
    session.recorder.record_click(
      { row: island1[0], col: island1[1] },
      result.old_count,
      result.new_count
    );
    session.recorder.save_board_state(serialize_state(session.game.value) as any);
  }
}

// handle exhausted toggle (right-click on island)
function on_exhausted_toggle(island: [number, number]) {
  session.game.value.toggle_exhausted(island);
  session.recorder.save_board_state(serialize_state(session.game.value) as any);
}
</script>

<template>
  <GameLayout :controller="session.controller" :definition="session.controller.state.value.definition">
    <HashiCanvas
      :key="session.canvas_key.value"
      :state="session.puzzle_state.value"
      @bridge-toggle="on_bridge_toggle"
      @exhausted-toggle="on_exhausted_toggle"
    />
  </GameLayout>
</template>
