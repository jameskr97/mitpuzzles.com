<script setup lang="ts">
import {
  Dialog,
  DialogScrollContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/core/components/ui/dialog";
import { computed, type PropType } from "vue";
import { useGameLayout } from "@/core/composables/useGameLayout.ts";
import { ACTIVE_GAMES } from "@/constants.ts";
import type { PuzzleController } from "@/core/games/types/puzzle-types.ts";

const layout = useGameLayout();
const props = defineProps({
  puzzle: { type: Object as PropType<PuzzleController>, required: true },
});

const game_type = props.puzzle.state_puzzle.value.definition.puzzle_type;
const game_entry = ACTIVE_GAMES[game_type];
const game_type_capitalized = computed(
  () => game_type.charAt(0).toUpperCase() + game_type.slice(1)
);
</script>

<template>
  <Dialog v-model:open="layout.instructions_visible.value">
    <DialogTrigger as-child>
      <slot name="trigger"></slot>
    </DialogTrigger>
    <DialogScrollContent class="max-w-2xl w-[calc(100%-2rem)]">
      <DialogHeader>
        <DialogTitle class="text-2xl">
          {{ game_type_capitalized }} instructions
        </DialogTitle>
      </DialogHeader>
      <component :is="game_entry.instructions" />
    </DialogScrollContent>
  </Dialog>
</template>
