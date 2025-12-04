<script setup lang="ts">
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuTrigger,
} from "@/core/components/ui/dropdown-menu";
import { Switch } from "@/core/components/ui/switch";
import { Label } from "reka-ui";
import { inject, computed } from "vue";
import type { PuzzleController } from "@/core/games/types/puzzle-types.ts";
import { useGameLayout } from "@/core/composables/useGameLayout.ts";
import { usePuzzleProgressStore } from "@/core/store/puzzle/usePuzzleProgressStore.ts";

const puzzle = inject<PuzzleController>("puzzle")!;
const layout = inject<ReturnType<typeof useGameLayout>>("layout")!;
const progress = usePuzzleProgressStore();

// @ts-ignore
const show_centiseconds = computed({
  get: () => progress.displayPrecision === "centiseconds",
  set: (value: boolean) => progress.set_display_precision(value)
});

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
          <Label for="tutorial-mode">{{ $t('freeplay:settings.tutorial_mode') }}</Label>
        </div>
      </DropdownMenuLabel>
      <DropdownMenuLabel>
        <div class="flex items-center space-x-2">
          <Switch v-model="layout.leaderboard_visible.value" id="leaderboard-visible" />
          <Label for="leaderboard-visible">{{ $t('freeplay:settings.show_leaderboard') }}</Label>
        </div>
      </DropdownMenuLabel>
<!--      <DropdownMenuLabel>-->
<!--        <div class="flex items-center space-x-2">-->
<!--          <Switch v-model="show_centiseconds" id="show-centiseconds" />-->
<!--          <Label for="show-centiseconds">Show Centiseconds</Label>-->
<!--        </div>-->
<!--      </DropdownMenuLabel>-->
    </DropdownMenuContent>
  </DropdownMenu>
</template>
