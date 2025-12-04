<script setup lang="ts">
import { computed, ref } from "vue";
import PuzzleRenderer from "@/core/components/PuzzleRenderer.vue";
import type { PuzzleDefinition } from "@/core/games/types/puzzle-types.ts";

const props = defineProps<{ puzzle: PuzzleDefinition }>();
defineEmits<{ click: [puzzle: PuzzleDefinition] }>();
const containerEl = ref<HTMLElement | null>(null);

const state_solved = computed(() => {
  if (!props.puzzle?.solution) return null
  return {
    definition: props.puzzle,
    board: props.puzzle.solution,
  }
})
</script>

<template>
  <div
    class="overflow-hidden border rounded-sm shadow-lg hover:-translate-y-0.5 transition-shadow cursor-pointer bg-white"
    @click="$emit('click', props.puzzle)"
  >
    <div
      ref="containerEl"
      class="@container aspect-square box-border place-items-center grid select-none pointer-events-none overflow-hidden p-1"
    >
      <PuzzleRenderer v-if="state_solved" :definition="props.puzzle" :state="state_solved" :parentEl="containerEl" />
      <div v-else class="text-xs text-gray-400 text-center">No solution</div>
    </div>
  </div>
</template>
