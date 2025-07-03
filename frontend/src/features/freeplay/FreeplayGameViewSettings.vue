<script setup lang="ts">
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Switch } from "@/components/ui/switch";
import { Label } from "reka-ui";
import { inject } from "vue";
import type { PuzzleController } from "@/services/game/engines/types.ts";
import { useGameLayout } from "@/composables/useGameLayout.ts";

const puzzle = inject<PuzzleController>("puzzle")!;
const layout = inject<ReturnType<typeof useGameLayout>>("layout")!;
</script>

<template>
  <DropdownMenu>
    <DropdownMenuTrigger>
      <v-icon name="io-settings-outline" :scale="1.5" class="mr-2 cursor-pointer" />
    </DropdownMenuTrigger>
    <DropdownMenuContent align="start">
      <DropdownMenuLabel>
        <div class="flex items-center space-x-2">
          <Switch v-model="puzzle.state_ui.value.tutorial_mode" id="tutorial-mode" />
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
