<script setup lang="ts">
import { inject, ref, onMounted, type PropType } from "vue";
import type { BoardContext } from "@/features/games.components/board.ts";
import { type BoardEvents, BoardInteraction } from "@/features/games.components/board.interaction.ts";

const props = defineProps({
  bind: {
    type: Object as PropType<Partial<BoardEvents>>,
    required: false,
    default: null,
  },
  bridge: {
    type: Object as PropType<any>,
    required: false,
    default: null,
  },
  enable_mobile_keyboard: {
    type: Boolean,
    required: false,
    default: false,
  },
});

const emits = defineEmits<{ (e: "inputEvent", payload: any): void }>();
const board = inject<BoardContext>("boardContext")!;
const interaction = new BoardInteraction(board, props.bind, (e: string, p: any) => {
  emits("inputEvent", { event_type: e, payload: p });
});

// Register this interaction instance with the bridge so other components can dispatch events
if (props.bridge) {
  props.bridge.registerBoardInteraction(interaction);
}

// Mobile keyboard support
const mobile_input_ref = ref<HTMLInputElement | null>(null);
const is_mobile = ref(false);
onMounted(() => is_mobile.value = 'ontouchstart' in window && window.innerWidth <= 768);

function handle_mobile_keydown(event: KeyboardEvent) {
  // pass allowable keys to the board interaction handler
  // TODO(james): we only allow sudoku keys for now, maybe make this configurable later
  if (/^[1-9]$/.test(event.key) || event.key === 'Backspace' || event.key === 'Delete') {
    interaction.onKeyDown(event); // trigger the board's keyboard handler directly with the original event
  }
}

// Set up mobile input focus when cells are clicked
// focus the hidden mobile input when a cell is clicked
function focus_mobile_input() {
  if (props.enable_mobile_keyboard && is_mobile.value && mobile_input_ref.value) {
    mobile_input_ref.value?.focus();
  }
}
if (props.enable_mobile_keyboard) interaction.setMobileFocusCallback(focus_mobile_input);
</script>

<template>
  <div>
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

    <!-- Hidden input for mobile numeric keyboard -->
    <input
      v-if="enable_mobile_keyboard && is_mobile"
      ref="mobile_input_ref"
      type="tel"
      inputmode="numeric"
      pattern="[1-9]"
      class="absolute opacity-0 pointer-events-none"
      style="left: -9999px"
      @keydown="handle_mobile_keydown"
      autocomplete="off"
      autocorrect="off"
      autocapitalize="off"
      spellcheck="false"
    />
  </div>
</template>
