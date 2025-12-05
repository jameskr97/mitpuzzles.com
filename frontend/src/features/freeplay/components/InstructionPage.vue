<script setup lang="ts">
import Container from "@/core/components/ui/Container.vue";
import { OverlayScrollbarsComponent } from "overlayscrollbars-vue";

defineProps({
  board_columns: {
    type: Number,
    default: 1,
  },
  board_max_width: {
    type: String,
    default: "max-w-60",
  },
});
</script>

<template>
  <div class="grid grid-rows-[1fr_1.5fr] gap-4 h-full">
    <!-- Instruction text -->
    <Container class="instruction-scroll overflow-y-scroll overflow-x-hidden bg-gray-50! p-3">
      <OverlayScrollbarsComponent v-if="$slots.instruction">
        <div class="flex flex-col gap-2">
          <slot name="instruction"></slot>
        </div>
      </OverlayScrollbarsComponent>
    </Container>


    <!-- Board grid - equal columns, items-start prevents stretching -->
    <div
      v-if="$slots.board"
      class="mx-auto w-full grid gap-4 items-start"
      :class="board_max_width"
      :style="{ gridTemplateColumns: `repeat(${board_columns}, 1fr)` }"
    >
      <slot name="board"></slot>
    </div>
  </div>
</template>
