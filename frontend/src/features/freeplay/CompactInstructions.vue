<script setup lang="ts">
import { useRoute } from "vue-router";
import { ACTIVE_GAMES, type PUZZLE_TYPES } from "@/constants.ts";
import { type PropType, ref } from "vue";
import type { PuzzleController } from "@/services/game/engines/types.ts";
import Container from "@/components/ui/Container.vue";
import { Separator } from "@/components/ui/separator";
import FreeplayGameViewInstructionModal from "@/features/freeplay/FreeplayGameViewInstructionModal.vue";
import { useGameLayout } from "@/composables/useGameLayout.ts";

const route = useRoute();
const gt = route.meta.game_type as PUZZLE_TYPES;
const game_entry = ACTIVE_GAMES[gt];
const is_game_rules_open = ref(true);
const layout = useGameLayout()

const props = defineProps({
  puzzle: { type: Object as PropType<PuzzleController>, required: true },
});
</script>

<template>
  <Container class="flex flex-col !bg-floralwhite">
    <div class="flex items-center justify-between cursor-pointer select-none w-full">
      <div class="flex items-center">
        <FreeplayGameViewInstructionModal>
          <template #trigger>
            <v-icon name="hi-information-circle" :scale="1.5" class="mr-2 cursor-pointer" />
          </template>
        </FreeplayGameViewInstructionModal>
        <span class="text-xl">Game Rules</span>
      </div>
      <v-icon
        name="md-keyboardarrowdown-round"
        :scale="1.5"
        :class="{ 'rotate-180': is_game_rules_open }"
        @click="is_game_rules_open = !is_game_rules_open"
      />
    </div>
    <template v-if="is_game_rules_open">
      <Separator class="my-2" />
      <component :is="game_entry.compact_instructions" :def="puzzle.state_puzzle.value.definition" />
      <Separator class="my-2" />
      <div class="text-center underline text-blue-500 cursor-pointer" @click="layout.instructions_visible.value = true">
        Show detailed instructions
      </div>
    </template>
  </Container>
</template>

<style scoped></style>
