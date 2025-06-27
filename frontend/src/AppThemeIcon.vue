<script setup lang="ts"></script>

<template>
  <div class="relative inline-block h-[1.2rem] w-[1.2rem]">
    <v-icon
      name="bi-moon-stars-fill"
      class="absolute h-[1.2rem] w-[1.2rem] rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0"
    />
    <v-icon
      name="bi-sun-fill"
      class="absolute h-[1.2rem] w-[1.2rem] rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100"
    />
    <span class="sr-only">Toggle theme</span>
  </div>
</template>

<style scoped></style>
