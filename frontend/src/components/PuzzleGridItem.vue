<script setup lang="ts">
import { ref } from "vue";
import PuzzleRenderer from "@/components/PuzzleRenderer.vue";
import type { PuzzleDefinition } from "@/services/game/engines/types.ts";

const props = defineProps<{ puzzle: PuzzleDefinition; }>();
const emit = defineEmits<{ click: [puzzle: PuzzleDefinition]; }>();
const containerEl = ref<HTMLElement | null>(null);
</script>

<template>
  <div
    class="rounded-lg border border-gray-200 overflow-hidden shadow-lg hover:-translate-y-0.5 transition-shadow cursor-pointer bg-white"
    @click="$emit('click', props.puzzle)"
  >
    <div
      ref="containerEl"
      class="@container aspect-square box-border place-items-center grid select-none pointer-events-none overflow-hidden p-1"
    >
      <PuzzleRenderer :definition="puzzle" :parentEl="containerEl" />
    </div>
  </div>
</template>
