<script setup lang="ts">
import { onMounted, onUnmounted, ref, useTemplateRef } from "vue";
import type { PuzzleDefinition } from "@/core/games/types/puzzle-types.ts";
import PuzzleRenderer from "@/core/components/PuzzleRenderer.vue";
import { useElementSize } from "@vueuse/core";

const props = withDefaults(
  defineProps<{
    puzzles: PuzzleDefinition[];
    enableInteraction?: boolean; // whether to enable keyboard navigation
    forceVisible?: boolean; // whether to force puzzles to be visible
  }>(),
  { enableInteraction: true, forceVisible: false },
);

const emit = defineEmits<{
  "view-puzzle": [index: number];
  "selection-changed": [fromIndex: number | null, toIndex: number];
}>();

// track if user has selected a puzzle locally
const selected_puzzle_index = ref<number | null>(null);

function handle_view_puzzle(index: number) {
  emit("view-puzzle", index);
}

function handle_select_puzzle(index: number) {
  if (index >= 0 && index < props.puzzles.length) {
    const previous_selection = selected_puzzle_index.value;

    // only update and emit if selection actually changed
    if (previous_selection !== index) {
      selected_puzzle_index.value = index;
      emit("selection-changed", previous_selection, index);
    }
  }
}

// keyboard navigation for choice phase
function handle_key_press(event: KeyboardEvent) {
  if (!props.enableInteraction) return;
  if (props.puzzles.length <= 0) return;
  if (!["ArrowLeft", "ArrowRight"].includes(event.key)) return;
  event.preventDefault();

  if (event.key === "ArrowLeft") {
    handle_view_puzzle(0);
    handle_select_puzzle(0);
  } else if (event.key === "ArrowRight") {
    handle_view_puzzle(1);
    handle_select_puzzle(1);
  }
}

function handle_puzzle_click(index: number) {
  if (!props.enableInteraction) return;
  handle_view_puzzle(index);
  handle_select_puzzle(index);
}

if (props.enableInteraction) {
  onMounted(() => document.addEventListener("keydown", handle_key_press));
  onUnmounted(() => document.removeEventListener("keydown", handle_key_press));
}

const puzzle_element = useTemplateRef("puzzle_element");
const { width, height } = useElementSize(puzzle_element);
</script>

<template>
  <div class="flex flex-col gap-4">
    <!-- puzzles grid -->
    <div class="grid grid-cols-2 gap-8">
      <div v-for="(puzzle, index) in puzzles" :key="puzzle.id" class="flex flex-col items-center gap-3">
        <div class="text-lg font-semibold">Puzzle {{ String.fromCharCode(65 + index) }}</div>
        <div class="p-2 border rounded shadow-sm cursor-pointer h-35 w-35" @click="handle_puzzle_click(index)">
          <PuzzleRenderer
            ref="puzzle_element"
            v-if="forceVisible || selected_puzzle_index === index"
            :definition="puzzle"
          />
          <div v-else
               class="flex items-center justify-center text-gray-400 text-center aspect-square"
               :class="{ 'width': width + 'px', 'height': height + 'px' }"
          >
            press {{ index === 0 ? "←" : "→" }} or <br />
            click to view
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped></style>
