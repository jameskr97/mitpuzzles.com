<script setup lang="ts">
import { useGameLayout } from "@/composables/useGameLayout.ts";
import { onMounted, onUnmounted } from "vue";
import { getGameScale } from "@/store/scale.ts";
import Container from "@/components/ui/Container.vue";
import GameViewControlBarTimer from "@/components/gameview.controlbar.timer.vue";
import GameViewControlBarSettings from "@/components/GameViewControlBarSettings.vue";
import { Slider } from "@/components/ui/slider";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import GameViewInstructionModal from "@/components/GameViewInstructionModal.vue";
import { getPuzzleDisplayName } from "@/utils.ts";
import { usePuzzleController } from "@/composables/usePuzzleController.ts";
import { useRoute } from "vue-router";
import { usePuzzleMetadataStore } from "@/store/puzzle.ts";
import type { PayloadPuzzleType } from "@/codegen/websocket/game.schema";

const route = useRoute();
const layout = useGameLayout();
const gt = route.meta.game_type as PayloadPuzzleType;
const puzzle = usePuzzleController(gt);
const { scale } = getGameScale();
const puzzle_metadata = usePuzzleMetadataStore();
////////////////////////////////////////////////////////////////////////
//// puzzle difficulty dropdown
function onDifficultySelect(diff: string[]) {
  if (document.activeElement instanceof HTMLElement) document.activeElement.blur();
  puzzle_metadata.setSelectedVariant(gt, diff);
  puzzle.request_new_puzzle();
}

////////////////////////////////////////////////////////////////////////
//// puzzle timer view
onMounted(() => puzzle.timer.start());
onUnmounted(() => puzzle.timer.stop());

////////////////////////////////////////////////////////////////////////
//// props
defineProps({
  showInstructionButton: { type: Boolean, default: true },
  showButtons: { type: Boolean, default: true },
  showVariant: { type: Boolean, default: true },
  showTimer: { type: Boolean, default: true },
});
</script>

<template>
  <Container class="w-full md:max-w-prose mt-2 md:mt-0 mx-auto">
    <div class="flex flex-col">
      <div class="flex flex-row w-full">
        <GameViewInstructionModal>
          <template #trigger>
            <v-icon name="hi-information-circle" :scale="1.5" class="mr-2 cursor-pointer" />
          </template>
        </GameViewInstructionModal>

        <GameViewControlBarSettings />
        <Slider :min="0" :max="100" :step="1" v-model="scale" class="mx-2" />
        <GameViewControlBarTimer />
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
        <Button variant="destructive" :disabled="puzzle.is_solved.value === true" @click="puzzle.request_puzzle_clear">
          Clear
        </Button>
        <Button variant="success" :disabled="puzzle.is_solved.value === true" @click="puzzle.request_puzzle_solved()">
          Submit
        </Button>
      </div>
    </div>
  </Container>
</template>
