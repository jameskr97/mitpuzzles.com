<script setup lang="ts">
import { ref, computed } from "vue";
import { remap } from "@/lib/util";
const props = defineProps({
  maxScale: { type: Number, required: false, default: 5 },
});
defineEmits<{
  (e: "resize", size: number): void;
  (e: "undo-clicked"): void;
  (e: "redo-clicked"): void;
  (e: "connect", ip: string): void;
}>();

// Board Variables (Internal to SFC)
const size_board = ref(30);
const game_id = ref("");

// Public Functions
const size_scaled = computed(() =>
  remap([0, 100], [1, props.maxScale], size_board.value)
);
defineExpose({ size_scaled });
</script>

<template>
  <div class="flex flex-col">
    <div class="flex flex-row items-center gap-2">
      <div class="tooltip" data-tip="Resize Game Board">
        <input
          v-model="size_board"
          type="range"
          min="0"
          max="100"
          class="range w-50"
        />
      </div>

      <div class="tooltip" data-tip="Undo Last Action">
        <v-icon name="fa-undo-alt" scale="1.5" />
      </div>

      <div class="tooltip" data-tip="Redo Last Action">
        <v-icon name="fa-redo-alt" scale="1.5" />
      </div>
    </div>
    <div class="flex flex-row gap-2 pt-2">
      <input v-model="game_id" type="text" class="input" />
      <button class="btn btn-primary">Connect</button>
    </div>
  </div>
</template>
