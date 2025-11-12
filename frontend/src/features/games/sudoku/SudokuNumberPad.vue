<script setup lang="ts">
import { computed } from "vue";
import type { PuzzleState } from "@/services/game/engines/types";
import type { createPuzzleInteractionBridge } from "@/features/games.composables/setupPuzzleInteractionBridge.ts";

const props = defineProps<{
  state: PuzzleState;
  interact?: ReturnType<typeof createPuzzleInteractionBridge>;
}>();

const emit = defineEmits<{
  (e: 'keyPress', key: string): void;
}>()

// array of buttons to make numbers with
const number_buttons = computed(() => {
  return Array.from({ length: props.state.definition.rows }, (_, i) => i + 1);
});
</script>

<template>
  <div v-if="state" class="flex flex-col items-center justify-center gap-2 select-none w-full">
    <!-- Number buttons in grid layout: 5 columns -->
    <div class="grid grid-cols-5 gap-2 minw">
      <button
        v-for="num in number_buttons"
        :key="num"
        class="box-border min-w-12 min-h-12 flex items-center justify-center text-lg font-semibold rounded-lg border-2 border-gray-500 bg-white hover:bg-gray-50 hover:border-gray-400 active:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-white outline-none cursor-pointer"
        @click="$emit('keyPress', num.toString())"
      >
        {{ num }}
      </button>

      <!-- Clear button (X) - always in the last position of the grid -->
      <button
        type="button"
        class="min-w-12 min-h-12 flex items-center justify-center text-lg font-bold rounded-lg border-2 border-red-300 bg-white text-red-600 hover:bg-red-50 hover:border-red-400 active:bg-red-100 disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-white outline-none cursor-pointer"
        @click="$emit('keyPress', 'Backspace')"
      >
        X
      </button>
    </div>
  </div>
</template>
