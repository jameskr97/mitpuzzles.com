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
import { useExperimentController } from "@/features/prolific.composables/useExperimentController.ts";


const route = useRoute()
const ctrl = useExperimentController(route.meta.experiment_key as string);

////////////////////////////////////////////////////////////////////////
//// props
defineEmits(['submitClick'])
</script>

<template>
  <Container class="w-full md:max-w-prose mt-2 md:mt-0 mx-auto">
    <div class="flex flex-col">
      <div class="flex flex-row w-full">
        <v-icon name="co-magnifying-glass" :scale="1.5" />
        <Slider :min="0" :max="100" :step="1" v-model="scale" class="mx-2" />
      </div>

      <!-- Buttons -->
      <div class="grid grid-cols-1 lg:grid-cols-4 w-full gap-1 mt-2">
        <Button variant="success"  @click="puzzle.request_puzzle_solved()">
          Done
        </Button>
      </div>
    </div>
  </Container>
</template>
