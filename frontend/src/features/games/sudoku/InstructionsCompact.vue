<script setup lang="ts">
import type { PuzzleDefinition } from "@/core/games/types/puzzle-types.ts";
import { computed } from "vue";

const props = defineProps<{
  def?: PuzzleDefinition;
}>();
const sqrt = computed(() => (props.def ? Math.sqrt(props.def.rows) : 3));
const word = computed(() => (sqrt.value === 3 ? "nine" : "four"));
</script>

<template>
  <div>
    <div class="mb-2" v-html="$t('puzzle:sudoku:compact.intro', { rows: def?.rows })"></div>
    <ul class="list-disc ml-4">
      <li v-html="$t('puzzle:sudoku:compact.rule_row', { rows: def?.rows })"></li>
      <li v-html="$t('puzzle:sudoku:compact.rule_col', { rows: def?.rows })"></li>
      <li v-html="$t('puzzle:sudoku:compact.rule_box', { word, sqrt, rows: def?.rows })"></li>
    </ul>
  </div>
</template>
