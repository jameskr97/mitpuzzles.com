<script setup lang="ts">
import { provide, reactive, toRefs } from "vue";
import type { PropType } from "vue";
import type { PuzzleModel } from "@/features/games/composables/PuzzleModelBase.js";
import { useGridPositions } from "@/features/games/components/useGridLayout.ts";
import { usePuzzleModelAdapter } from "@/features/games/composables/PuzzleModelAdapter.ts";
import type { BoardContext } from "@/features/games/components/board.ts";

const props = defineProps({
  // Board Dimensions
  rows: { type: Number, required: true },
  cols: { type: Number, required: true },
  cellSize: { type: Number, required: false, default: 10 },
  scale: { type: Number, required: false, default: 1 },
  // Board Styling
  borderConfig: { type: Object, required: false, default: () => ({}) },
  gap: { type: Number, required: false, default: 1 },
  // Gutters
  gutterTop: { type: Number, required: false, default: 0 },
  gutterLeft: { type: Number, required: false, default: 0 },
  gutterRight: { type: Number, required: false, default: 0 },
  gutterBottom: { type: Number, required: false, default: 0 },
  // Model
  model: { type: Object as PropType<PuzzleModel<any>>, required: false },
});
const rprops = toRefs(props);
const model = props.model ? usePuzzleModelAdapter(props.model) : null;

////////////////////////////////////////////////////////////////////////////////
//////// Provide a single board context object to children
const boardContext = reactive({
  rows: rprops.rows,
  cols: rprops.cols,
  cellSize: rprops.cellSize,
  scale: rprops.scale,
  gap: rprops.gap,
  borderConfig: rprops.borderConfig,
  gutters: { top: rprops.gutterTop, left: rprops.gutterLeft, right: rprops.gutterRight, bottom: rprops.gutterBottom },
  model,
});
provide("boardContext", boardContext);
const p = useGridPositions(boardContext as BoardContext);
</script>

<template>
  <div class="relative h-full w-full mx-auto flex justify-center items-start">
    <div
      :style="{
        transform: `scale(${scale})`,
        width: p.fullWidth.value + 'px',
        height: p.fullHeight.value + 'px',
      }"
      class="relative origin-top"
    >
      <slot />
    </div>
  </div>
</template>
