<script setup lang="ts">
import GameLayout from "@/components/ui/layout/game.layout.vue";
import sudoku from "./sudoku.vue";
</script>

<template>
  <div class="justify-center w-full flex flex-row">
    <GameLayout title="Minesweeper" v-slot="{ controlbar }">
      <sudoku
        :scale="controlbar.size_scaled"
      />
    </GameLayout>
  </div>
</template>
