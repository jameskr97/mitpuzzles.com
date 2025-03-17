<script setup lang="ts">
import { computed, useSlots } from "vue";

const props = defineProps({
  rows: { type: Number, required: true },
  cols: { type: Number, required: true },
  size: { type: Number, required: false },
  cellClass: { type: String, required: false, default: "" },
  rowClass: { type: String, required: false, default: "" },
  gridClass: { type: String, required: false, default: "" },

  // Outer grid classes
  topClass: { type: String, required: false, default: "" },
  bottomClass: { type: String, required: false, default: "" },
  leftClass: { type: String, required: false, default: "" },
  rightClass: { type: String, required: false, default: "" },
});

defineEmits<{
  (e: "cellClick", cell: any): void;
  (e: "cellRightClick", cell: any): void;
  (e: "cellEnter", cell: any): void;
  (e: "cellLeave", cell: any): void;
  (e: "mouseDown", cell: any): void;
  (e: "mouseUp", cell: any): void;
  (e: "gridEnter"): void;
  (e: "gridLeave"): void;
  (e: "keyDown", cell: any): void;
  (e: "keyUp", cell: any): void;
}>();

const slots = useSlots();

const gridStyle = computed(() => {
  const left = slots.left ? "min-content" : 0;
  const right = slots.right ? "min-content" : 0;
  const top = slots.top ? "min-content" : 0;
  const bottom = slots.bottom ? "min-content" : 0;

  return {
    gridTemplateColumns: `${left} auto ${right}`,
    gridTemplateRows: `${top} auto ${bottom}`,
  };
});

const cellDimensions = computed(() => {
  if(props.size) {
    return { width: props.size + 'rem', height: props.size + 'rem' };
  } else {
    return {};
  }
});
</script>

<template>
  <div class="grid grid-cols-3 leading-[0.92]" :style="gridStyle">
    <!-- EXTERNAL GRID TOP -->
    <div v-if="$slots.top" class="w-full flex flex-row col-start-2">
      <div
        v-for="(_col, ic) in cols"
        :class="['grow', topClass]"
        :style="{ fontSize: '2rem' }"
      >
        <slot name="top" :col="ic"></slot>
      </div>
    </div>

    <!-- EXTERNAL GRID BOTTOM -->
    <div
      v-if="$slots.bottom"
      class="w-full flex flex-row col-start-2 row-start-3"
    >
      <div
        v-for="(_col, ic) in cols"
        :class="['h-full grow', bottomClass]"
        :style="{ width: size + 'rem', height: size + 'rem' }"
      >
        <slot name="bottom" :col="ic" :size="size"></slot>
      </div>
    </div>

    <!-- EXTERNAL GRID LEFT -->
    <div v-if="$slots.left" class="flex flex-col col-start-1 row-start-2">
      <div v-for="(_row, ir) in rows"
          :class="['grow', leftClass]"
          :style="{ fontSize: '2rem' }">
        <slot name="left" :row="ir" :size="size"></slot>
      </div>
    </div>

    <!-- EXTERNAL GRID RIGHT  -->
    <div
      v-if="$slots.right"
      class="w-full flex flex-col col-start-3 row-start-2"
    >
      <div
        v-for="(_row, ir) in rows"
        :class="['h-full grow', rightClass]"
        :style="{ width: size + 'rem', height: size + 'rem' }"
      >
        <slot name="right" :row="ir" :size="size"></slot>
      </div>
    </div>

    <!-- CENTER GAME GRID -->
    <div :class="['w-full h-full col-start-2 row-start-2', gridClass]">
      <div @mouseenter="$emit('gridEnter')" @mouseleave="$emit('gridLeave')">
        <div v-for="(row, ir) in rows" :class="['h-full flex flex-row', rowClass]">
          <!-- prettier-ignore -->
          <div
            v-for="(col, ic) in cols"
            :class="['w-full h-full flex flex-row aspect-square grow', cellClass]"
            :style="cellDimensions"
            @click="$emit('cellClick', { row: ir, col: ic })"
            @contextmenu.prevent="$emit('cellRightClick', { row: ir, col: ic })"
            @mousedown="$emit('mouseDown', { row: ir, col: ic })"
            @mouseup="$emit('mouseUp', { row: ir, col: ic, input_event: $event })"
            @keydown="$emit('keyDown', { row: ir, col: ic, input_event: $event })"
            @keyup="$emit('keyUp', { row: ir, col: ic, input_event: $event })"
            @mouseenter="$emit('cellEnter', { row: ir, col: ic })"
            @mouseleave="$emit('cellLeave', { row: ir, col: ic })"
            tabindex="-1"
          >
            <div class="w-full focus:outline-none grow" tabindex="-1">
              <slot
                name="cell"
                class="h-full"
                :row="row - 1"
                :col="col - 1"
                :index="ir * rows + ic"
                :size="size"
              >
              </slot>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
