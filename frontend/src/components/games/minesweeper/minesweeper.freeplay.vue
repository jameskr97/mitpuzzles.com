<script setup lang="ts">
import minesweeper from "./Minesweeper.vue";
</script>

<template>
  <div class="container justify-center w-full p-2 flex">
    <div class="flex gap-2 flex-col">
      <p class="text-3xl">Minesweeper (three boards)</p>

      <div class="flex flex-row">
        <minesweeper :rows="10" :cols="10" :mine-count="10" :scale="3" />
      </div>

      <!-- <minesweeper
        :rows="20"
        :cols="30"
        :mine-count="1"
        :scale="1.5"
      /> -->
    </div>
  </div>
</template>
