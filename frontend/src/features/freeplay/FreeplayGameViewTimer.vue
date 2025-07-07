<script setup lang="ts">
import { inject, ref } from "vue";
import type { PuzzleController } from "@/services/game/engines/types.ts";
import { useGameAttemptStore } from "@/store/useGameAttemptStore.ts";

const puzzle = inject<PuzzleController>("puzzle")!;
const attemptStore = useGameAttemptStore();

const showMilliseconds = ref(false);
</script>

<template>
  <div class="text-2xl text-right font-mono">
    <span>{{
      attemptStore.getFormattedTime(
        puzzle.state_puzzle.value.definition.puzzle_type,
        showMilliseconds ? "milliseconds" : "seconds",
      )
    }}</span>
  </div>
</template>
