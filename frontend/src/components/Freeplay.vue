<script setup lang="ts">
import { ACTIVE_GAMES } from "@/constants.ts";
import { useRoute } from "vue-router";
import FreeplayGameView from "@/features/freeplay/FreeplayGameView.vue";
import { useFreeplayPuzzle } from "@/composables/useFreeplayPuzzle.ts";
import { createPuzzleInteractionBridge } from "@/features/games.composables/setupPuzzleInteractionBridge.ts";
import { usePuzzleScaleStore } from "@/store/puzzle/usePuzzleScaleStore.ts";
import Container from "@/components/ui/Container.vue";
import type { BattleshipsMeta } from "@/services/game/engines/types.ts";
import SudokuNumberPad from "@/features/games/sudoku/SudokuNumberPad.vue";
import { ref } from "vue";
import { useGameLayout } from "@/composables/useGameLayout.ts";

const route = useRoute();
const gt = route.meta.game_type as string;
const puzzle = await useFreeplayPuzzle(gt);
const game_entry = ACTIVE_GAMES[gt];
const scaleStore = usePuzzleScaleStore();
const bridge = createPuzzleInteractionBridge(puzzle, false);

// if the game defines it's own default behaviors, we will use those
if (game_entry["defaultBehaviors"].length !== 0) {
  game_entry["defaultBehaviors"].forEach((behavior: any) => behavior(puzzle, bridge));
} else {
  if (bridge) {
    // otherwise, we will use the default behaviors
    bridge.addDefaultBehaviors();
  }
}
</script>

<template>
  <FreeplayGameView :puzzle="puzzle" class="mt-2 [touch-action:manipulation] !mx-2">
    <component
      :is="game_entry.component"
      :state="puzzle.state_puzzle.value"
      :scale="scaleStore.getScaleRemapped(gt)"
      :interact="bridge"
    />

    <template #game-below>
      <Container class="min-w-fit" v-if="puzzle.state_puzzle.value.definition.puzzle_type === 'sudoku'">
        <SudokuNumberPad
          :state="puzzle.state_puzzle.value"
          :interact="bridge"
        />
      </Container>
    </template>

    <template #game-right>
      <Container
        v-if="puzzle.state_puzzle.value.definition.puzzle_type === 'battleships'"
        class="items-center grid grid-cols-[auto_1fr] gap-2 text-sm w-40 auto-rows-min"
      >
        <div class="flex gap-0.5">
          <div class="w-5 h-5 bg-black rounded-l-full"></div>
          <div class="w-5 h-5 bg-black"></div>
          <div class="w-5 h-5 bg-black rounded-r-full"></div>
        </div>
        <div>{{ (puzzle.state_puzzle.value.definition.meta as BattleshipsMeta).ships_dict["3"] }}</div>
        <div class="flex gap-0.5">
          <div class="w-5 h-5 bg-black rounded-l-full"></div>
          <div class="w-5 h-5 bg-black rounded-r-full"></div>
        </div>
        <div>{{ (puzzle.state_puzzle.value.definition.meta as BattleshipsMeta).ships_dict["2"] }}</div>
        <div class="flex gap-0.5">
          <div class="w-5 h-5 bg-black rounded-full "></div>
        </div>
        <div>{{ (puzzle.state_puzzle.value.definition.meta as BattleshipsMeta).ships_dict["1"] }}</div>
      </Container>
    </template>
  </FreeplayGameView>
</template>
