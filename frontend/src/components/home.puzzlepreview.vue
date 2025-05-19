<script setup lang="ts">
import { ref } from "vue";

const props = defineProps({
  title: { type: String, required: true },
  page: { type: String, required: true },
  component: { type: Object, required: false },
  state: { type: Object, required: false },
});

const container = ref();
const puzzleRef = ref();
</script>

<template>
  <router-link :to="{ name: 'game-' + page }">
    <div class="flex flex-col">
      <div ref="container" class="@container aspect-square place-items-center grid select-none pointer-events-none">
        <component :ref="puzzleRef" :is="component" :state="state" />
      </div>
      <div class="divider my-0 py-0 h-full"></div>
      <div class="p-1 mx-auto">{{ props.title }}</div>
    </div>
  </router-link>
</template>
