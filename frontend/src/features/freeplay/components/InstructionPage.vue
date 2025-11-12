<script setup lang="ts">/**
 * Instruction page layout - stacked with text above, board(s) below.
 * Board area is a grid - multiple boards get equal column widths.
 */
import Container from "@/components/ui/Container.vue";

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
      <div v-if="$slots.instruction" class="flex flex-col gap-2">
        <slot name="instruction"></slot>
      </div>
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

<style scoped>
/*
Source - https://stackoverflow.com/a
Posted by Cumulo Nimbus
Retrieved 2025-12-03, License - CC BY-SA 3.0
*/
.instruction-scroll::-webkit-scrollbar {
  -webkit-appearance: none;
  width: 10px;
}

.instruction-scroll::-webkit-scrollbar-thumb {
  border-radius: 5px;
  background-color: rgba(0, 0, 0, 0.5);
  -webkit-box-shadow: 0 0 1px rgba(255, 255, 255, 0.5);
}

.instruction-scroll::-webkit-scrollbar-track {
  background-color: rgba(0, 0, 0, 0.1);
  border-radius: 5px;
}
</style>
