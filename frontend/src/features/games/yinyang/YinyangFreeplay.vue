<script setup lang="ts">
import GameLayout from "@/features/freeplay/GameLayout.vue";
import YinyangCanvas from "./YinyangCanvas.vue";
import { useYinyangGame, YinyangCell } from "./useYinyangGame";
import { useCellDragHandlers, useDemoGame } from "@/core/games/composables";
import type { PuzzleDefinition } from "@/core/games/types/puzzle-types";

const B = YinyangCell.CLUE_BLACK;
const W = YinyangCell.CLUE_WHITE;
const _ = YinyangCell.EMPTY;

const definition: PuzzleDefinition = {
  id: "yinyang-demo-6x6",
  puzzle_type: "yinyang",
  puzzle_size: "6x6",
  puzzle_difficulty: "easy",
  rows: 6,
  cols: 6,
  initial_state: [
    [B, _, _, _, _, _],
    [W, _, _, _, _, _],
    [_, _, _, B, B, _],
    [_, W, _, W, _, _],
    [_, _, _, W, _, _],
    [_, _, _, _, _, B],
  ],
  solution_hash: "111111e1a11111b1b1a11a11e1",
  meta: {},
};

const demo = useDemoGame({
  puzzle_type: "yinyang",
  definition,
  create_game: useYinyangGame,
});

const { on_cell_click, on_cell_drag } = useCellDragHandlers(demo.game, demo.recorder);
</script>

<template>
  <GameLayout :controller="demo.controller" :definition="demo.controller.state.value.definition">
    <YinyangCanvas
      :key="demo.canvas_key.value"
      :state="demo.puzzle_state.value as any"
      @cell-click="on_cell_click"
      @cell-drag="on_cell_drag"
      @cell-enter="demo.on_cell_enter"
      @cell-leave="demo.on_cell_leave"
    />
  </GameLayout>
</template>
