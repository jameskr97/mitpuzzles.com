<script setup lang="ts">
// This is isolated into it's own component
import { useCurrentPuzzle } from "@/composables/useCurrentPuzzle.ts";
const puzzle = await useCurrentPuzzle();
</script>

<template>
  <div class="text-2xl text-right font-mono">
    <span>{{ puzzle.timer.display_time }}</span>
  </div>
</template>

