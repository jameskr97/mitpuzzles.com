<script setup lang="ts">
import { useGameLayout } from "@/composables/useGameLayout.ts";
import { computed, inject, onMounted, onUnmounted } from "vue";
import Container from "@/components/ui/Container.vue";
import FreeplayGameViewTimer from "@/features/freeplay/FreeplayGameViewTimer.vue";
import GameViewControlBarSettings from "@/features/freeplay/FreeplayGameViewSettings.vue";
import { Slider } from "@/components/ui/slider";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import FreeplayGameViewInstructionModal from "@/features/freeplay/FreeplayGameViewInstructionModal.vue";
import { getPuzzleDisplayName } from "@/utils.ts";
import { useRoute } from "vue-router";
import { usePuzzleMetadataStore } from "@/store/puzzle.ts";
import type { PUZZLE_TYPES } from "@/constants.ts";
import { useGameScalesStore, useGameAttemptStore } from "@/store/game.ts";
import type { PuzzleController } from "@/services/game/engines/types.ts";

const route = useRoute();
const gt = route.meta.game_type as PUZZLE_TYPES;
const puzzle = inject<PuzzleController>("puzzle")!;
const layout = inject<ReturnType<typeof useGameLayout>>("layout")!;
const scaleStore = useGameScalesStore();
const attemptStore = useGameAttemptStore();
const puzzle_metadata = usePuzzleMetadataStore();

////////////////////////////////////////////////////////////////////////
//// puzzle difficulty dropdown
async function onDifficultySelect(diff: string[]) {
  if (document.activeElement instanceof HTMLElement) document.activeElement.blur();
  puzzle_metadata.setSelectedVariant(gt, diff);
  await puzzle.request_new_puzzle();
}

const currentScale = computed({
  get: () => [scaleStore.getScale(gt)],
  set: (value: number[]) => scaleStore.setScale(gt, value[0]),
});

////////////////////////////////////////////////////////////////////////
//// puzzle timer view
onMounted(() => attemptStore.startTimer(gt));
onUnmounted(() => attemptStore.stopTimer(gt));

////////////////////////////////////////////////////////////////////////
//// props
defineProps({
  showInstructionButton: { type: Boolean, default: true },
  showButtons: { type: Boolean, default: true },
  showVariant: { type: Boolean, default: true },
  showTimer: { type: Boolean, default: true },
  showSettings: { type: Boolean, default: true },
});
</script>

<template>
  <Container class="w-full md:max-w-prose mt-2 md:mt-0 mx-auto">
    <div class="flex flex-col">
      <div class="flex flex-row w-full">
        <FreeplayGameViewInstructionModal>
          <template #trigger>
            <v-icon name="hi-information-circle" :scale="1.5" class="mr-2 cursor-pointer" />
          </template>
        </FreeplayGameViewInstructionModal>

        <GameViewControlBarSettings />
        <v-icon name="co-magnifying-glass" :scale="1.5" />
        <Slider :min="0" :max="100" :step="1" class="mx-2" v-model="currentScale" />
        <FreeplayGameViewTimer />
      </div>

      <!-- Buttons -->
      <div v-if="showButtons" class="grid grid-cols-2 lg:grid-cols-4 w-full gap-1 mt-2">
        <DropdownMenu>
          <DropdownMenuTrigger>
            <Button class="w-full" variant="outline">
              <span>Difficulty</span>
              <v-icon name="md-arrowdropdown" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent class="w-full">
            <DropdownMenuItem
              v-for="variant in puzzle_metadata.getVariants(gt)"
              :key="variant[0] + '.' + variant[1]"
              @click="onDifficultySelect(variant)"
            >
              <span>{{ getPuzzleDisplayName(variant) }}</span>
              <v-icon name="bi-check" v-if="puzzle_metadata.doesMatchCurrentVariant(gt, variant)" />
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
        <Button @click="puzzle.request_new_puzzle">New Puzzle</Button>
        <Button
          variant="destructive"
          :disabled="puzzle.state_puzzle.value.solved === true"
          @click="puzzle.clear_puzzle"
        >
          Clear
        </Button>
        <Button variant="success" :disabled="puzzle.state_puzzle.value.solved === true" @click="puzzle.check_solution">
          Submit
        </Button>
      </div>
    </div>
  </Container>
</template>
