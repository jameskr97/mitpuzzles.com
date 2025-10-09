<script setup lang="ts">
import { useGameLayout } from "@/composables/useGameLayout.ts";
import { computed, inject, onMounted, onUnmounted } from "vue";
import Container from "@/components/ui/Container.vue";
import FreeplayGameViewTimer from "@/features/freeplay/FreeplayGameViewTimer.vue";
import GameViewControlBarSettings from "@/features/freeplay/FreeplayGameViewSettings.vue";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
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
import type { PUZZLE_TYPES } from "@/constants.ts";
import type { PuzzleController } from "@/services/game/engines/types.ts";
import { usePuzzleMetadataStore } from "@/store/puzzle/usePuzzleMetadataStore.ts";
import { usePuzzleScaleStore } from "@/store/puzzle/usePuzzleScaleStore.ts";

const route = useRoute();
const gt = route.meta.game_type as PUZZLE_TYPES;
const puzzle = inject<PuzzleController>("puzzle")!;
const scaleStore = usePuzzleScaleStore();
const puzzle_metadata = usePuzzleMetadataStore();

////////////////////////////////////////////////////////////////////////
//// puzzle difficulty dropdown
async function onDifficultySelect(diff: string[]) {
  if (document.activeElement instanceof HTMLElement) document.activeElement.blur();
  puzzle_metadata.set_selected_variant(gt, diff);
  await puzzle.request_new_puzzle();
}

const currentScale = computed({
  get: () => [scaleStore.getScale(gt)],
  set: (value: number[]) => scaleStore.setScale(gt, value[0]),
});

////////////////////////////////////////////////////////////////////////
//// props
defineProps({
  showInstructionButton: { type: Boolean, default: true },
  showButtons: { type: Boolean, default: true },
  showVariant: { type: Boolean, default: true },
  showTimer: { type: Boolean, default: true },
  showSettings: { type: Boolean, default: true },
});

onMounted(() => {
  function handle_keydown(e: KeyboardEvent) {
    if (e.key === "+" || e.key === "=" || e.key === "-") {
      const increment = (e.key === "+" || e.key === "=") ? 5 : -5;
      e.preventDefault();
      const new_scale = Math.max(0, Math.min(100, currentScale.value[0] + increment));
      scaleStore.setScale(gt, new_scale);
    }
  }

  window.addEventListener("keydown", handle_keydown);
  onUnmounted(() => window.removeEventListener("keydown", handle_keydown));
});
</script>

<template>
  <Container class="w-full md:max-w-prose mt-2 md:mt-0 mx-auto">
    <div class="flex flex-col">
      <div class="flex flex-row w-full items-center">
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
