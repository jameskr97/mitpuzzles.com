<script setup lang="ts">
import { inject, type PropType } from "vue";
import type { BoardContext } from "@/features/games.components/board.ts";
import { type BoardEvents, BoardInteraction } from "@/features/games.components/board.interaction.ts";

const props = defineProps({
  bind: {
    type: Object as PropType<Partial<BoardEvents>>,
    required: false,
    default: null,
  },
});

const emits = defineEmits<{ (e: "inputEvent", payload: any): void }>();
const board = inject<BoardContext>("boardContext")!;
const interaction = new BoardInteraction(board, props.bind, (e: string, p: any) => {
  emits("inputEvent", { event_type: e, payload: p });
});
</script>

<template>
  <div
    class="absolute z-9999 w-full h-full focus:outline-none user-select-none"
    tabindex="0"
    @contextmenu.prevent
    @mousedown="interaction.onMouseDown"
    @mousemove="interaction.onMouseMove"
    @mouseup="interaction.onMouseUp"
    @mouseenter="interaction.onBoardEnter"
    @mouseleave="interaction.onBoardLeave"
    @keydown="interaction.onKeyDown"
    @dragstart.prevent
  ></div>
</template>
