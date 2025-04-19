<script setup lang="ts">
import { ACTIVE_GAMES } from "@/main.ts";
import { useRoute } from "vue-router";
import { useCurrentPuzzle } from "@/composables/useCurrentPuzzle.ts";
import GameLayout from "@/components/layout/game.layout.vue";
import { getGameScale } from "@/store/scale.ts";
import MarkdownIt from "markdown-it";

// load game state + data
const route = useRoute();
const game_entry = ACTIVE_GAMES[route.meta.game_type as string];
const puzzle = await useCurrentPuzzle();
const scale = getGameScale();

// load game rules as markdown
const md = MarkdownIt({ html: true, linkify: true, typographer: true });
const game_rules_raw = await game_entry.instructions();
const instructionHTML = md.render(game_rules_raw.default);

const on_game_event = (event_type: string, payload: object) => puzzle.record_event(event_type, payload);
</script>

<template>
  <GameLayout>
    <template #instructions>
      <div class="prose" v-html="instructionHTML"></div>
    </template>

    <template v-slot:default>
      <component
        v-if="puzzle.can_render_board.value"
        :is="game_entry.component"
        :state="puzzle.state"
        :scale="scale.scale_remapped.value"
        @game-event="on_game_event"
      />
    </template>
  </GameLayout>
</template>
