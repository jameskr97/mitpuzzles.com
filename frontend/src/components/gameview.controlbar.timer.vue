<script setup lang="ts">
import { usePuzzleController } from "@/composables/usePuzzleController.ts";
import { useRoute } from "vue-router";
import type { PayloadPuzzleType } from "@/codegen/websocket/game.schema";
const route = useRoute();
const puzzle = usePuzzleController(route.meta.game_type as PayloadPuzzleType);
</script>

<template>
  <div class="text-2xl text-right font-mono">
    <span>{{puzzle.timer.display_time}}</span>
  </div>
</template>
