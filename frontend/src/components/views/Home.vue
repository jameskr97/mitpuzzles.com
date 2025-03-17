<script setup lang="ts">
import HomeGamebox from "@/components/ui/elements/home.gamebox.vue";
import PuzzleMinesweeeper from "@/components/games/minesweeper/minesweeper.puzzle.vue";
import PuzzleTents from "@/components/games/tents/tents.puzzle.vue";
import PuzzleSudoku from "@/components/games/sudoku/sudoku.puzzle.vue";
import PuzzleKakurasu from "@/components/games/kakurasu/kakurasu.puzzle.vue";
import { useAppConfig } from "@/store/config";
const settings = useAppConfig();
settings.fetchGameSettings();
</script>

<template>
  <div class="grid md:grid-cols-3 gap-2 items-end">
    <HomeGamebox title="Minesweeper"><PuzzleMinesweeeper /></HomeGamebox>
    <HomeGamebox title="Tents"><PuzzleTents /></HomeGamebox>
    <HomeGamebox title="Sudoku"><PuzzleSudoku /></HomeGamebox>
    <HomeGamebox title="Kakurasu"><PuzzleKakurasu /></HomeGamebox>
  </div>
</template>
