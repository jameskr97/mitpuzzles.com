<script setup lang="ts">
import { computed, type PropType, provide, reactive, toRefs } from "vue";
import { useGridPositions, useGridLayout } from "@/features/games.components/useGridLayout.ts";
import type { BoardContext } from "@/features/games.components/board.ts";
import { useElementSize } from "@vueuse/core";

const props = defineProps({
  // Board Dimensions
  rows: { type: Number, required: true },
  cols: { type: Number, required: true },
  cellSize: { type: Number, required: false, default: 40 },
  scale: { type: Number, required: false },
  // Board Styling
  borderConfig: { type: Object, required: false, default: () => ({}) },
  gap: { type: Number, required: false, default: 1 },
  // Gutters
  gutterTop: { type: Number, required: false, default: 0 },
  gutterLeft: { type: Number, required: false, default: 0 },
  gutterRight: { type: Number, required: false, default: 0 },
  gutterBottom: { type: Number, required: false, default: 0 },
  parentEl: { type: Object as PropType<HTMLElement>, required: false },
});
const rprops = toRefs(props);

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
});
provide("boardContext", boardContext);
const p = useGridPositions(boardContext as BoardContext);
const l = useGridLayout(boardContext as BoardContext);
const parent = useElementSize(rprops?.parentEl!);
const calculatedScale = computed(() => {
  if (props.scale) return props.scale;
  if (!rprops.parentEl) return 1; // no scale and no parent element? return default of 1;
  if (!parent.width.value || !parent.height.value || !p.fullWidth.value || !p.fullHeight.value) return 1;
  return Math.min(parent.width.value / p.fullWidth.value, parent.height.value / p.fullHeight.value);
});

defineExpose({
  width: p.fullWidth,
  height: p.fullHeight,
});
</script>

<template>
  <div
    class="relative flex select-none"
    :style="{
      width: p.fullWidth.value * calculatedScale + 'px',
      height: p.fullHeight.value * calculatedScale + 'px',
    }"
  >
    <div
      :style="{
        transform: `scale(${calculatedScale})`,
        left:
          (l.has_left_gutter.value || l.has_right_gutter.value ? p.gameGridOuterGap.value * calculatedScale : 0) + 'px',
        top:
          (l.has_top_gutter.value || l.has_bottom_gutter.value ? p.gameGridOuterGap.value * calculatedScale : 0) + 'px',
        // left: p.gameGridOuterGap.value * scale + 'px',
        // top:  p.gameGridOuterGap.value * scale + 'px',
        width: p.fullWidth.value + 'px',
        height: p.fullHeight.value + 'px',
      }"
      class="absolute origin-top-left"
      :key="calculatedScale"
    >
      <slot />
    </div>
  </div>
</template>
