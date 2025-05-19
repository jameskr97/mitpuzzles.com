<script setup lang="ts">
import { useGameLayout } from "@/composables/useGameLayout.ts";
const layout = useGameLayout();
</script>

<template>
  <div class="z-100 bg-white flex flex-col gap-2 order-1 md:order-first md:col-start-1">
    <div class="border-2 border-black shadow rounded p-2">
      <div class="flex flex-col md:w-full">
        <div class="flex flex-row align-middle justify-between">
          <p class="text-xl text-center md:text-left">Game Instructions</p>
          <v-icon class="mt-1 cursor-pointer" name="io-close" @click="layout.instructions_visible.value = false" />
        </div>
        <div class="divider divider-vertical p-0 m-0"></div>
        <ul class="list-inside list-decimal text-xs">
          <slot name="instructions"></slot>
        </ul>
      </div>
    </div>
  </div>
</template>
