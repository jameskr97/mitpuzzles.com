<script setup lang="ts">
defineProps({
  layout_mode: {
    type: String,
    default: "split",
    validator: (value: string) => ["split", "content-only", "board-focus", "side-by-side"].includes(value)
  },
  content_ratio: { type: String, default: "1:1" },
});
</script>

<template>
  <div
    :class="{
      'grid grid-rows-[auto_1fr] gap-2': layout_mode === 'split',
      'flex flex-col': layout_mode === 'content-only' || layout_mode === 'board-focus',
      'grid grid-cols-2 gap-2': layout_mode === 'side-by-side'
    }"
    :style="{
      gridTemplateRows: layout_mode === 'split' && content_ratio !== '1:1' ?
        (content_ratio === '2:1' ? 'auto 1fr' :
         content_ratio === '1:2' ? 'auto 2fr' :
         'auto 1fr') : undefined,
      gridTemplateColumns: layout_mode === 'side-by-side' ?
        (content_ratio === '2:1' ? '2fr 1fr' :
         content_ratio === '1:2' ? '1fr 2fr' :
         '1fr 1fr') : undefined
    }"
  >
    <!-- Instruction Content -->
    <div
      v-if="$slots.instruction"
      class="overflow-y-auto h-48 border rounded-md p-3 bg-gray-50"
      :class="{
        'flex-1 h-auto border-none bg-transparent p-0': layout_mode === 'content-only',
        'flex-shrink-0 h-32': layout_mode === 'board-focus'
      }"
    >
      <slot name="instruction"></slot>
    </div>

    <!-- Board Content -->
    <div v-if="$slots.board" class="min-h-100 mx-auto">
      <slot name="board"></slot>
    </div>
  </div>
</template>

<style scoped></style>
