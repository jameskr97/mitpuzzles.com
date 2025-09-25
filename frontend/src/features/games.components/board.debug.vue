<script setup lang="ts">
import type { BoardContext } from "@/features/games.components/board.ts";
import { useGridPositions } from "@/features/games.components/useGridLayout.ts";
import { inject } from "vue";

const boardContext = inject<BoardContext>("boardContext")!;
const p = useGridPositions(boardContext);
</script>

<template>
  <!-- prettier-ignore -->
  <div>
      <div class="absolute bg-blue-500 -z-9999"     :style="{width: p.topGutterWidth.value + 'px',    height: p.topGutterHeight.value + 'px',     top: p.topGutterStartY.value + 'px',    left: p.topGutterStartX.value + 'px'}"></div>
      <div class="absolute bg-yellow-500 -z-9999"   :style="{width: p.leftGutterWidth.value + 'px',   height: p.leftGutterHeight.value + 'px',    top: p.leftGutterStartY.value + 'px',   left: p.leftGutterStartX.value + 'px' }"></div>
      <div class="absolute bg-green-500 -z-9999"    :style="{width: p.rightGutterWidth.value + 'px',  height: p.rightGutterHeight.value + 'px',   top: p.rightGutterStartY.value + 'px',  left: p.rightGutterStartX.value + 'px' }"></div>
      <div class="absolute bg-purple-500 -z-9999"   :style="{width: p.bottomGutterWidth.value + 'px', height: p.bottomGutterHeight.value + 'px',  top: p.bottomGutterStartY.value + 'px', left: p.bottomGutterStartX.value + 'px' }"></div>
      <div class="absolute bg-red-500 -z-9999"      :style="{width: p.gameGridWidth.value + 'px',     height: p.gameGridHeight.value + 'px',      top: p.gameGridStartY.value + 'px',     left: p.gameGridStartX.value+ 'px'}"></div>
  </div>
</template>
