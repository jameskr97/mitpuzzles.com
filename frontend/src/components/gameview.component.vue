<!-- GameLayout.vue -->
<script setup lang="ts">
import { getGameScale } from "@/store/scale";
import GameViewControlBar from "@/components/gameview.controlbar.vue";
import GameViewAlert from "@/components/gameview.alert.vue";
import GameViewViolations from "@/components/gameview.violations.vue";
import { useCurrentPuzzle } from "@/composables/useCurrentPuzzle.ts";

const puzzle = await useCurrentPuzzle();
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

        <div class="grid grid-cols-[1fr_2fr_1fr] items-start">
          <!-- Game Violations -->
          <GameViewViolations
            v-if="puzzle.tutorial_mode.value"
            :violations="puzzle.state.value?.violations ?? []"
            class="row-start-2 col-span-3 md:col-start-1 md:row-start-1 md:col-span-1"
          />

          <!-- The GameContent itself -->
          <div
            class="z-100 order-first md:order-1 col-start-2 grid grid-cols-1 place-items-center mb-2 mx-2 items-center max-h-fit"
          >
            <GameViewAlert />
            <div class="select-none" :class="{ 'pointer-events-none': puzzle.is_solved.value }">
              <!--              {{store}}-->
              <!--              {{puzzle}}-->
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
