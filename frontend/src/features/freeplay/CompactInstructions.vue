<script setup lang="ts">
import { ACTIVE_GAMES } from "@/constants.ts";
import { type PropType, ref, inject } from "vue";
import type { PuzzleController } from "@/core/games/types/puzzle-types.ts";
import type { GameLayoutReturn } from "@/core/composables/useGameLayout";
import Container from "@/core/components/ui/Container.vue";
import { Separator } from "@/core/components/ui/separator";
import { InstructionModal } from "@/features/freeplay/components";

const is_game_rules_open = ref(true);
const layout = inject<GameLayoutReturn>("game-layout")!

const props = defineProps({
  puzzle: { type: Object as PropType<PuzzleController>, required: true },
});
const game_entry = ACTIVE_GAMES[props.puzzle.state_puzzle.value.definition.puzzle_type];
</script>

<template>
  <Container class="flex flex-col !bg-floralwhite">
    <div class="flex items-center justify-between cursor-pointer select-none w-full">
      <div class="flex items-center">
        <InstructionModal :puzzle="puzzle">
          <template #trigger>
            <v-icon name="hi-information-circle" :scale="1.5" class="mr-2 cursor-pointer" />
          </template>
        </InstructionModal>
        <span class="text-xl">{{ $t('freeplay:instructions.game_rules') }}</span>
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
        {{ $t('freeplay:instructions.show_detailed') }}
      </div>
    </template>
  </Container>
</template>

<style scoped></style>
