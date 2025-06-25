<script setup lang="ts">
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Switch } from "@/components/ui/switch";
import { Label } from "reka-ui";
import { useCurrentPuzzle } from "@/composables/useCurrentPuzzle.ts";
import { useGameLayout } from "@/composables/useGameLayout.ts";
import { usePuzzleController } from "@/composables/usePuzzleController.ts";
import { useRoute } from "vue-router";
import type { PayloadPuzzleType } from "@/codegen/websocket/game.schema";

// const puzzle = await useCurrentPuzzle()
const route = useRoute();
const puzzle = usePuzzleController(route.meta.game_type as PayloadPuzzleType);
const layout = useGameLayout();
</script>

<template>
  <DropdownMenu>
    <DropdownMenuTrigger>
      <v-icon name="io-settings-outline" :scale="1.5" class="mr-2 cursor-pointer" />
    </DropdownMenuTrigger>
    <DropdownMenuContent align="start">
      <DropdownMenuLabel>
        <div class="flex items-center space-x-2">
          <Switch v-model="puzzle.tutorial_mode.value" id="tutorial-mode" />
          <Label for="tutorial-mode">Tutorial Mode</Label>
        </div>
      </DropdownMenuLabel>
      <DropdownMenuLabel>
        <div class="flex items-center space-x-2">
          <Switch v-model="layout.leaderboard_visible.value" id="leaderboard-visible" />
          <Label for="leaderboard-visible">Show Leaderboard</Label>
        </div>
      </DropdownMenuLabel>
    </DropdownMenuContent>
  </DropdownMenu>
</template>
