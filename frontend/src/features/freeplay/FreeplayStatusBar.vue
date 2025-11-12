<script setup lang="ts">
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import Container from "@/components/ui/Container.vue";
import { Switch } from "@/components/ui/switch";
import { inject, type PropType } from "vue";
import type { PuzzleController } from "@/services/game/engines/types.ts";
import { getPuzzleDisplayName } from "@/utils.ts";

const props = defineProps({
  puzzle: { type: Object as PropType<PuzzleController>, required: true },
});
const puzzle = inject<PuzzleController>("puzzle") || props.puzzle!;
</script>

<template>
  <Container class="w-full md:max-w-prose mx-auto h-12">
    <div class="m-0 p-0 grid grid-cols-3 text-xl">
      <!-- Tutorial Mode Toggle -->
      <div class="flex items-center gap-2">
        <Switch v-model="puzzle.state_ui.value.tutorial_mode" id="tutorial-toggle" />
        <Label for="tutorial-toggle" class="cursor-pointer font-normal">{{ $t('freeplay:settings.tutorial_mode') }}</Label>
      </div>
      <span class="col-start-2 text-center items-center">
        {{ getPuzzleDisplayName(puzzle.current_puzzle_variant.value) }}
      </span>
      <Badge
        v-if="puzzle.state_ui.value.show_solved_state"
        :variant="puzzle.state_puzzle.value.solved ? 'blue' : 'destructive'"
        class="justify-self-end text-nowrap text-base"
      >
        <span v-if="puzzle.state_puzzle.value.solved">{{ $t('freeplay:status.solved') }}</span>
        <span v-else>{{ $t('freeplay:status.not_solved') }}</span>
      </Badge>
    </div>
  </Container>
</template>

<style scoped></style>
