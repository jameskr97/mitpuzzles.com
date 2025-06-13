<script setup lang="ts">
import { useCurrentPuzzle } from "@/composables/useCurrentPuzzle.ts";
const puzzle = await useCurrentPuzzle();
</script>

<template>
  <div class="w-full mb-2">
    <div v-if="puzzle.is_solved.value === true" role="alert" class="alert alert-success flex flex-row justify-start">
      <v-icon name="fa-check-circle" scale="1.5" />
      <span>Your solution is correct</span>
      <button class="btn btn-outline ml-auto" @click="puzzle.request_new_puzzle">New puzzle</button>
    </div>

    <div
      v-else-if="puzzle.is_solved.value === false"
      role="alert"
      class="alert alert-error flex flex-row justify-start mb-2"
    >
      <v-icon name="io-close" scale="1.5" />
      <span> Not quite! </span>
    </div>
  </div>
</template>
