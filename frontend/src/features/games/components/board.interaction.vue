<script setup lang="ts">
import { inject } from "vue";
import type { BoardContext } from "@/features/games/components/board.ts";
import { BoardInteraction } from "@/features/games/components/board.interaction.ts";

const emits = defineEmits<{
  (e: "inputEvent", payload: any): void;
}>();
const board = inject<BoardContext>("boardContext")!;
const interaction = new BoardInteraction(board, board.model, (e: string, p: any) => {
  emits("inputEvent", { event_type: e, payload: p });
});
</script>

<template>
  <div
    class="absolute z-9999 w-full h-full focus:outline-none"
    tabindex="0"
    @contextmenu.prevent
    @mousedown.prevent="interaction.onMouseDown"
    @mousemove.passive="interaction.onMouseMove"
    @mouseup.prevent="interaction.onMouseUp"
    @keydown.passive="interaction.onKeyDown"
  ></div>
</template>
