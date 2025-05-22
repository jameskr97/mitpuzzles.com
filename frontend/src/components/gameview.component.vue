<!-- GameLayout.vue -->
<script setup lang="ts">
import { useGameLayout } from "@/composables/useGameLayout";
import { getGameScale } from "@/store/scale";
import GameViewControlBar from "@/components/gameview.controlbar.vue";
import GameInstructions from "@/components/gameview.instructions.vue";
import GameViewAlert from "@/components/gameview.alert.vue";
import { useCurrentPuzzle } from "@/composables/useCurrentPuzzle.ts";

const puzzle = await useCurrentPuzzle();
const layout = useGameLayout();
const { scale_remapped } = getGameScale();
</script>

<template>
  <div class="flex flex-col md:flex-row h-full">
    <div class="w-full mx-auto p-2">
      <div class="h-full flex flex-col">
        <!-- GAME CONTROL BAR -->
        <GameViewControlBar />

        <!-- Divider between control bar and game content -->
        <div class="divider divider-vertical mb-2 mt-0"></div>

        <div class="grid gap-2 md:gap-0 md:grid-cols-[1fr_2fr_1fr] h-full items-start">
          <!-- Game Instructions -->
          <GameInstructions v-show="layout.instructions_visible.value">
            <template #instructions>
              <slot name="instructions"></slot>
            </template>
          </GameInstructions>

          <!-- The GameContent itself -->
          <div
            class="z-100 order-first md:order-1 grid grid-cols-1 place-items-center mb-2 mx-2"
            :class="{ 'md:col-start-2': !layout.instructions_visible.value }"
          >
            <GameViewAlert />

            <div class="select-none" :class="{ 'pointer-events-none': puzzle.is_solved.value }">
              <slot name="default" :scale="scale_remapped"></slot>
            </div>
          </div>

          <!-- Leaderboard container -->
          <!--          <GameLeaderboard v-if="layout.leaderboard_visible.value" />-->
        </div>
      </div>
    </div>
  </div>
</template>
