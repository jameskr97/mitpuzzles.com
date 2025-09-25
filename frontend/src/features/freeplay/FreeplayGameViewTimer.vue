<script setup lang="ts">
import { inject, ref } from "vue";
import type { PuzzleController } from "@/services/game/engines/types.ts";
import { usePuzzleProgressStore } from "@/store/puzzle/usePuzzleProgressStore.ts";

const puzzle = inject<PuzzleController>("puzzle")!;
const progressStore = usePuzzleProgressStore();
</script>

<template>
  <div class="text-2xl text-right font-mono">
    <span>
       {{ progressStore.get_formatted_time(puzzle.state_puzzle.value.definition.puzzle_type) }}
    </span>
  </div>
</template>
