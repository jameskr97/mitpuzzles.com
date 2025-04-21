<script setup lang="ts">
import { computed, useSlots } from "vue";
import useGridLayout from "@/composables/useGridLayout";
defineEmits<{
  (e: "cellClick", cell: any): void;
  (e: "cellRightClick", cell: any): void;
  (e: "cellEnter", cell: any): void;
  (e: "cellLeave", cell: any): void;
  (e: "mouseDown", cell: any): void;
  (e: "mouseUp", cell: any): void;
  (e: "gridEnter", metadata: any): void;
  (e: "gridLeave", metadata: any): void;
  (e: "keyDown", cell: any): void;
  (e: "keyUp", cell: any): void;
  (e: "clickGutterRight", cell: any): void;
  (e: "clickGutterLeft", cell: any): void;
  (e: "clickGutterTop", cell: any): void;
  (e: "clickGutterBottom", cell: any): void;
}>();

const slots = useSlots();
const props = defineProps({
  // Grid Dimensions
  rows: { type: Number, required: true },
  cols: { type: Number, required: true },
  cellSize: { type: Number, required: false, default: 10 },

  // Grid Layout
  gap: { type: Number, required: false, default: 1 },
  scale: { type: Number, required: false },
  fontSize: { type: Number, required: false, default: 10 },

  // Grid Customization
  borderRadius: { type: Number, required: false, default: 0 },
  classGameCell: { type: String, required: false, default: "" },
  classGameGrid: { type: String, required: false, default: "" },
});

const layout = useGridLayout(props.rows, props.cols, slots, props.cellSize, props.gap);

const cellStyle = computed(() => (index: number) => {
  const adjustedSize = props.cellSize; // Pixel size
  const fontSize = Math.max(12, adjustedSize * 0.2).toFixed(0); // Font size in pixels

  const col = index % props.cols;
  const row = Math.floor(index / props.cols);

  const styles: Record<string, string> = {
    fontSize: `${fontSize}px`,
    width: `${adjustedSize}px`,
    height: `${adjustedSize}px`,
  };

  // Optional radius on corners
  if (index === 0) styles.borderTopLeftRadius = `${props.borderRadius}px`;
  if (col === props.cols - 1 && row === 0) styles.borderTopRightRadius = `${props.borderRadius}px`;
  if (index === (props.rows - 1) * props.cols) styles.borderBottomLeftRadius = `${props.borderRadius}px`;
  if (index === props.rows * props.cols - 1) styles.borderBottomRightRadius = `${props.borderRadius}px`;

  return styles;
});

const coord = (ci: number) => ({
  row: Math.floor(ci / props.cols),
  col: ci % props.cols,
  index: ci,
});

const dims_px = computed(() => ({
  width: layout.dims.NUM_ROWS * props.cellSize + (layout.dims.NUM_ROWS - 1) * props.gap,
  height: layout.dims.NUM_COLS * props.cellSize + (layout.dims.NUM_COLS - 1) * props.gap,
}));

defineExpose({ dims_px });
</script>

<template>
  <div
    class="grid origin-top"
    :style="[
      layout.rootGridStyle.value,
      {
        transform: `scale(${props.scale})`,
      },
    ]"
  >
    <div v-if="$slots.top" class="grid grid-cols-subgrid" :style="layout.styleGutterTop.value">
      <div
        v-for="(_, ic) in cols" :style="cellStyle(ic)"
        @click="$emit('clickGutterTop', { col: ic, input_event: $event, ts: Date.now() })"
      >
        <div class="@container static overflow-hidden focus:outline-none w-full h-full">
          <div class="text-[70cqw] w-full h-full focus:outline-none mb-10">
            <slot name="top" :row="ic" :col="ic"></slot>
          </div>
        </div>
      </div>
    </div>

    <div v-if="$slots.bottom" class="grid grid-cols-subgrid" :style="layout.styleGutterBottom.value">
      <div
        v-for="(_, ic) in cols" :style="cellStyle(ic)"
        @click="$emit('clickGutterBottom', { col: ic, input_event: $event, ts: Date.now() })"
      >
        <div class="@container static overflow-hidden focus:outline-none w-full h-full">
          <div class="text-[70cqw] w-full h-full focus:outline-none">
            <slot name="bottom" :row="ic" :col="ic"></slot>
          </div>
        </div>
      </div>
    </div>

    <div v-if="$slots.left" class="grid grid-rows-subgrid" :style="layout.styleGutterLeft.value">
      <div
        v-for="(_, ir) in rows" :style="cellStyle(ir)"
        @click="$emit('clickGutterLeft', { row: ir, input_event: $event, ts: Date.now() })"
      >
        <div class="@container static overflow-hidden focus:outline-none w-full h-full">
          <div class="text-[70cqw] w-full h-full focus:outline-none">
            <slot name="left" :row="ir" :col="ir"></slot>
          </div>
        </div>
      </div>
    </div>

    <div v-if="$slots.right" class="grid grid-rows-subgrid" :style="layout.styleGutterRight.value">
      <div
        v-for="(_, ir) in rows" :style="cellStyle(ir)"
        @click="$emit('clickGutterRight', { row: ir, input_event: $event, ts: Date.now() })"
      >
        <div class="@container static overflow-hidden focus:outline-none w-full h-full">
          <div class="text-[70cqw] w-full h-full focus:outline-none">
            <slot name="right" :row="ir" :col="ir"></slot>
          </div>
        </div>
      </div>
    </div>

    <div
      class="grid grid-rows-subgrid grid-cols-subgrid border-[1px] -top-[1px] -left-[1px] bg-black"
      :style="layout.styleGameGrid.value"
    >
      <div
        v-for="(_, ci) in cols * rows"
        class="@container bg-white overflow-hidden focus:outline-none text-[70cqw]"
        :class="[classGameCell]"
        :style="[cellStyle(ci)]"
        @click="$emit('cellClick', { ...coord(ci), input_event: $event, ts: Date.now() })"
        @contextmenu.prevent="$emit('cellRightClick', { ...coord(ci), input_event: $event, ts: Date.now() })"
        @mousedown="$emit('mouseDown', { ...coord(ci), input_event: $event, ts: Date.now() })"
        @mouseup="$emit('mouseUp', { ...coord(ci), input_event: $event, ts: Date.now() })"
        @keydown="$emit('keyDown', { ...coord(ci), input_event: $event, ts: Date.now() })"
        @keyup="$emit('keyUp', { ...coord(ci), input_event: $event, ts: Date.now() })"
        @mouseenter="$emit('cellEnter', { ...coord(ci), ts: Date.now() })"
        @mouseleave="$emit('cellLeave', { ...coord(ci), ts: Date.now() })"
        tabindex="-1"
      >
        <div class="text-[70cqw] w-full h-full select-none">
          <slot name="cell" v-bind="coord(ci)"></slot>
        </div>
      </div>
    </div>
  </div>
</template>
