<script setup lang="ts">
import { computed } from "vue";
import { ACTIVE_GAMES } from "@/constants.ts";
import type { PuzzleState, PuzzleDefinition } from "@/core/games/types/puzzle-types.ts";

interface Props {
  definition: PuzzleDefinition;
  state?: Partial<PuzzleState>;
  scale?: number;
}
const props = defineProps<Props>();

const current_puzzle_component = computed(() => {
  const puzzle_type = props.definition.puzzle_type;
  const game_config = ACTIVE_GAMES[puzzle_type];
  if (!game_config) {
    console.warn(`Unknown puzzle type: ${puzzle_type}`);
    return null;
  }
  return game_config.component;
});

// if no state provided, create a basic state from the definition
const puzzle_state = computed(() => {
  if (props.state) return props.state;
  return {
    definition: props.definition,
    board: props.definition.initial_state,
  };
});
</script>

<template>
  <component
    v-if="current_puzzle_component"
    :is="current_puzzle_component"
    :state="puzzle_state"
    :scale="scale"
  />
  <div v-else class="p-4 text-red-500">Unknown puzzle type: {{ definition.puzzle_type }}</div>
</template>
