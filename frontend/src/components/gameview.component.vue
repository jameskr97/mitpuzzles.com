<!-- GameLayout.vue -->
<script setup lang="ts">
import { getGameScale } from "@/store/scale";
import GameViewControlBar from "@/components/gameview.controlbar.vue";
import GameViewViolations from "@/components/gameview.violations.vue";
import GameViewLeaderboard from "@/components/gameview.leaderboard.vue";
import { Alert, AlertTitle } from "@/components/ui/alert";
import { useGameLayout } from "@/composables/useGameLayout.ts";
import Container from "@/components/ui/Container.vue";
import { Badge } from "@/components/ui/badge";
import { getPuzzleDisplayName } from "@/utils.ts";
import { usePuzzleController } from "@/composables/usePuzzleController.ts";
import type { PayloadPuzzleType } from "@/codegen/websocket/game.schema";
import { useRoute } from "vue-router";

const route = useRoute();
const puzzle = usePuzzleController(route.meta.game_type as PayloadPuzzleType);
const layout = useGameLayout();
const { scale_remapped } = getGameScale();
</script>

<template>
  <div class="flex flex-col mx-auto">
    <GameViewControlBar />

    <div v-if="puzzle.show_solved_state.value" class="w-full text-center max-w-prose mx-auto">
      <Alert variant="info" v-if="puzzle.is_solved.value === true" class="w-full mt-2">
        <AlertTitle>Your solution is correct</AlertTitle>
      </Alert>
      <Alert
        variant="destructive"
        v-else-if="puzzle.is_solved.value === false"
        class="w-full mt-2 border-red-500 bg-red-500/10"
      >
        <AlertTitle>Not Quite!</AlertTitle>
      </Alert>
    </div>

    <Container v-else class="mt-2 min-w-[65ch] mx-auto">
      <div class="m-0 p-0 grid grid-cols-3">
        <Badge variant="default" v-if="puzzle.tutorial_mode.value" class="justify-self-start text-nowrap">
          Tutorial Mode
        </Badge>
        <span class="col-start-2 text-center">
          {{ getPuzzleDisplayName(puzzle.selected_variant.value) }}
        </span>
      </div>
    </Container>

    <div class="grid grid-cols-2 gap-2">
      <div class="mx-auto col-span-full m-2 justify-self-center flex justify-center items-center">
        <div class="select-none origin-center transform-gpu" :class="{ 'pointer-events-none': puzzle.is_solved.value }">
          <Container>
            <slot name="default" :scale="scale_remapped"></slot>
          </Container>
        </div>
      </div>

      <div class="flex flex-col mx-auto gap-2 col-span-2">
        <GameViewViolations v-if="puzzle.tutorial_mode.value" :violations="puzzle.state.value?.violations ?? []" />
        <GameViewLeaderboard v-if="layout.leaderboard_visible.value" />
      </div>
    </div>
  </div>
</template>
