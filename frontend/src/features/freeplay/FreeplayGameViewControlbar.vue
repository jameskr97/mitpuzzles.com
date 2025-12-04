<script setup lang="ts">
import { useGameLayout } from "@/core/composables/useGameLayout.ts";
import { computed, inject, onMounted, onUnmounted, type PropType } from "vue";
import Container from "@/core/components/ui/Container.vue";
import FreeplayGameViewTimer from "@/features/freeplay/FreeplayGameViewTimer.vue";
import GameViewControlBarSettings from "@/features/freeplay/FreeplayGameViewSettings.vue";
import { Slider } from "@/core/components/ui/slider";
import { Switch } from "@/core/components/ui/switch";
import { Label } from "@/core/components/ui/label";
import { Button } from "@/core/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/core/components/ui/dropdown-menu";
import { getPuzzleDisplayName } from "@/utils.ts";
import { useRoute } from "vue-router";
import type { PUZZLE_TYPES } from "@/constants.ts";
import type { PuzzleController } from "@/core/games/types/puzzle-types.ts";
import { usePuzzleMetadataStore } from "@/core/store/puzzle/usePuzzleMetadataStore.ts";
import { usePuzzleScaleStore } from "@/core/store/puzzle/usePuzzleScaleStore.ts";

////////////////////////////////////////////////////////////////////////
//// props
const props = defineProps({
  puzzle: { type: Object as PropType<PuzzleController>, required: false},
  showInstructionButton: { type: Boolean, default: true },
  showButtons: { type: Boolean, default: true },
  showVariant: { type: Boolean, default: true },
  showTimer: { type: Boolean, default: true },
  showSettings: { type: Boolean, default: true },
});

const route = useRoute();
const puzzle = inject<PuzzleController>("puzzle") || props.puzzle!;
const gt = puzzle.state_puzzle.value.definition.puzzle_type as PUZZLE_TYPES;

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
        <FreeplayGameViewTimer :puzzle="puzzle" />
      </div>

      <!-- Buttons -->
      <div v-if="showButtons" class="grid grid-cols-2 lg:grid-cols-4 w-full gap-1 mt-2">
        <DropdownMenu>
          <DropdownMenuTrigger>
            <Button class="w-full" variant="outline">
              <span>{{ $t('freeplay:control.difficulty') }}</span>
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
        <Button @click="puzzle.request_new_puzzle">{{ $t('freeplay:control.new_puzzle') }}</Button>
        <Button
          variant="destructive"
          :disabled="puzzle.state_puzzle.value.solved === true"
          @click="puzzle.clear_puzzle"
        >
          {{ $t('ui:action.clear') }}
        </Button>
        <Button variant="success" :disabled="puzzle.state_puzzle.value.solved === true" @click="puzzle.check_solution">
          {{ $t('ui:action.submit') }}
        </Button>
      </div>
    </div>
  </Container>
</template>
