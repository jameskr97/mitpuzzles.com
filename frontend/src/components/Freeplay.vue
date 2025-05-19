<script setup lang="ts">
import { ACTIVE_GAMES } from "@/main.ts";
import { useRoute } from "vue-router";
import { getGameScale } from "@/store/scale.ts";
import MarkdownIt from "markdown-it";
import GameViewComponent from "@/components/gameview.component.vue";
import { useCurrentPuzzle } from "@/composables/useCurrentPuzzle.ts";
import { createPuzzleInteractionBridge } from "@/features/games.composables/setupPuzzleInteractionBridge.ts";

// load game state + data
const puzzle = await useCurrentPuzzle();
const interact = createPuzzleInteractionBridge(puzzle);
const scale = getGameScale();

// load game rules as markdown
const route = useRoute();
const md = MarkdownIt({ html: true, linkify: true, typographer: true });
const game_entry = ACTIVE_GAMES[route.meta.game_type as string];
const game_rules_raw = await game_entry.instructions();
const instructionHTML = md.render(game_rules_raw.default);
</script>

<template>
  <GameViewComponent>
    <template #instructions>
      <div class="prose prose-ul:leading-5" v-html="instructionHTML"></div>
    </template>

    <template #default>
      <div v-if="!puzzle.is_ready">Loading...</div>
      <component
        v-if="puzzle.is_ready.value"
        :is="game_entry.component"
        :interact="interact"
        :state="puzzle.state.value"
        :scale="scale.scale_remapped.value"
      />
    </template>
  </GameViewComponent>
</template>
