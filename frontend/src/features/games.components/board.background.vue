<script setup lang="ts">
import { useGridLayout, useGridPositions } from "@/features/games.components/useGridLayout.ts";
import type { BoardContext } from "@/features/games.components/board.ts";
import { inject, computed } from "vue";

const board = inject<BoardContext>("boardContext")!;
const layout = useGridLayout(board);
const positions = useGridPositions(board);

const game_grid_gap = computed(() => board.borderConfig.outer?.thickness ?? 0);
</script>

<template>
  <div
    class="absolute"
    :style="{
      left: positions.gameGridStartX.value - game_grid_gap + 'px',
      top: positions.gameGridStartY.value - game_grid_gap + 'px',
      width: layout.gameGridWidth.value + game_grid_gap * 2 + 'px',
      height: layout.gameGridHeight.value + game_grid_gap * 2 + 'px',
    }"
  ></div>
</template>
