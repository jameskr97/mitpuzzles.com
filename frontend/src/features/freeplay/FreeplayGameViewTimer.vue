<script setup lang="ts">
import { inject, ref } from "vue";
import type { PuzzleController } from "@/core/games/types/puzzle-types.ts";
import { usePuzzleProgressStore } from "@/core/store/puzzle/usePuzzleProgressStore.ts";

const props = defineProps<{
  puzzle?: PuzzleController
}>();

const puzzle = inject<PuzzleController>("puzzle") || props.puzzle!;
const progressStore = usePuzzleProgressStore();
</script>

<template>
  <div class="text-2xl text-right font-mono">
    <span>
       {{ progressStore.get_formatted_time(puzzle.state_puzzle.value.definition.puzzle_type) }}
    </span>
  </div>
</template>
