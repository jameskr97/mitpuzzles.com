<script setup lang="ts">
import { useAppConfig } from '@/store/config';
const settings = useAppConfig();
settings.fetchGameSettings();
</script>

<template>
  <div class="flex p-4 flex-col rounded shadow-2xl rev justify-center mx-auto sm:w-120 text-xl border">

    <p class="text-4xl">Welcome to mitpuzzles.com</p>
    <div class="divider m-0"></div>
    <p>This is an early version of a logic games website.</p>
    <div class="divider m-0"></div>
    <p>Currently, only minesweeper with previously used stimuli will be randomly presented.</p>
    <div class="divider m-0"></div>
    <div class="flex flex-col sm:flex-row w-full justify-between gap-2">
      <router-link to="/minesweeper" class="btn btn-primary">Play Minesweeper Puzzle</router-link>
    </div>
  </div>
</template>
