<script setup lang="ts">
const props = defineProps({
  maxScale: { type: Number, required: false, default: 5 },
  settings: { type: Object, required: true },
});
defineEmits<{
  (e: "resized", size: number): void;
  (e: "undo-clicked"): void;
  (e: "redo-clicked"): void;
}>();

const size_board = props.settings.getScale();
</script>

<template>
  <div class="flex flex-col w-full">
    <div class="flex flex-row items-center gap-2 px-2">
      <div class="tooltip w-full" data-tip="Resize Game Board">
        <input
          v-model="size_board"
          type="range"
          min="0"
          max="100"
          class="range w-full!"
        />
      </div>

      <div class="tooltip" data-tip="Undo Last Action">
        <v-icon class="ms-auto" name="fa-undo-alt" scale="1.5" />
      </div>

      <div class="tooltip" data-tip="Redo Last Action">
        <v-icon name="fa-redo-alt" scale="1.5" />
      </div>
    </div>
  </div>
</template>
