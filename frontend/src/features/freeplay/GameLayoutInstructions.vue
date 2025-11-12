<script setup lang="ts">
/**
 * GameLayoutInstructions - Instructions panel for freeplay games
 *
 * Works with the new GameController interface.
 */
import { ref } from "vue";
import type { GameDefinition } from "@/types/game-controller";
import { ACTIVE_GAMES } from "@/constants";
import Container from "@/components/ui/Container.vue";
import { Separator } from "@/components/ui/separator";
import { useGameLayout } from "@/composables/useGameLayout";

const props = defineProps<{
  puzzle_type: string;
  definition: GameDefinition;
}>();

const is_rules_open = ref(true);
const layout = useGameLayout();
const game_entry = ACTIVE_GAMES[props.puzzle_type];
</script>

<template>
  <Container class="flex flex-col !bg-floralwhite">
    <div class="flex items-center justify-between cursor-pointer select-none w-full">
      <div class="flex items-center">
        <v-icon
          name="hi-information-circle"
          :scale="1.5"
          class="mr-2 cursor-pointer"
          @click="layout.instructions_visible.value = true"
        />
        <span class="text-xl">{{ $t("freeplay:instructions.game_rules") }}</span>
      </div>
      <v-icon
        name="md-keyboardarrowdown-round"
        :scale="1.5"
        :class="{ 'rotate-180': is_rules_open }"
        @click="is_rules_open = !is_rules_open"
      />
    </div>

    <template v-if="is_rules_open">
      <Separator class="my-2" />
      <component
        v-if="game_entry?.compact_instructions"
        :is="game_entry.compact_instructions"
        :def="definition"
      />
      <Separator class="my-2" />
      <div
        class="text-center underline text-blue-500 cursor-pointer"
        @click="layout.instructions_visible.value = true"
      >
        {{ $t("freeplay:instructions.show_detailed") }}
      </div>
    </template>
  </Container>
</template>
