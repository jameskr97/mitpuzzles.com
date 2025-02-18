<script setup lang="ts">
import GameLayout from "@/components/ui/layout/game.layout.vue";
import MinesweeperPuzzle from "@/components/games/minesweeper/minesweeper.puzzle.vue";
import { getRandomPuzzle } from "@/api/app";

const p = await getRandomPuzzle();
</script>

<template>

  <div class="justify-center w-full flex flex-row">
    <GameLayout title="Minesweeper" v-slot="{ controlbar }">
      <MinesweeperPuzzle
        :puzzle="p"
        :scale="controlbar.size_scaled"
      />
    </GameLayout>
  </div>
</template>
