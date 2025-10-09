<script setup lang="ts">
import type { PuzzleDefinition } from "@/services/game/engines/types.ts";
import { computed } from "vue";

const props = defineProps<{
  def?: PuzzleDefinition;
}>();
const sqrt = computed(() => (props.def ? Math.sqrt(props.def.rows) : 3));
const word = computed(() => (sqrt.value === 3 ? "nine" : "four"));
</script>

<template>
  <div>
    <div class="mb-2">
      Fill every empty cell in the {{ def?.rows }}×{{ def?.rows }} grid with a digit 1–{{ def?.rows }} so that:
    </div>
    <ul class="list-disc ml-4">
      <li>Each row contains each digit 1–{{ def?.rows }} exactly once.</li>
      <li>Each column contains each digit 1–{{ def?.rows }} exactly once.</li>
      <li>Each of the {{ word }} {{ sqrt }}×{{ sqrt }} boxes contains each digit 1–{{ def?.rows }} exactly once.</li>
    </ul>
  </div>
</template>
