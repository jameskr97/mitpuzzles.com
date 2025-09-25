<script setup lang="ts">
defineProps({
  imgClass: { type: String, required: false, default: "" },
});
</script>

<template>
  <router-link to="/">
    <img src="/assets/logo.dark.png" alt="mitpuzzles.com logo" :class="[imgClass, 'block dark:hidden']" />
    <img src="/assets/logo.light.png" alt="mitpuzzles.com logo" :class="[imgClass, 'hidden dark:block']" />
  </router-link>
</template>

<style scoped></style>
