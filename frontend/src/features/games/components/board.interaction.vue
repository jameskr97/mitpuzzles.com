<script setup lang="ts">
import { inject } from "vue";
import type { BoardContext } from "@/features/games/components/board.ts";
import { BoardInteraction } from "@/features/games/components/board.interaction.ts";

const board = inject<BoardContext>("boardContext")!;
const interaction = new BoardInteraction(board, board.model);
</script>

<template>
  <div
    class="absolute z-9999 w-full h-full focus:outline-none"
    tabindex="0"
    @mousedown="interaction.onMouseDown"
    @mousemove="interaction.onMouseMove"
    @mouseup="interaction.onMouseUp"
    @keydown="interaction.onKeyDown"
  ></div>
</template>
