<script setup lang="ts">
import GameControlBar from "@/components/ui/game/game.controlbar.vue";
import { ref } from 'vue';

const controlbar = ref<InstanceType<typeof GameControlBar>>()

defineProps({
  title: { type: String, required: true },
  maxScale: { type: Number, required: false, default: 5 },
});
</script>

<template>
  <div class="flex flex-col items-center border-5 border-red-500">
    <p class="text-2xl underline">{{ title }}</p>
    <GameControlBar ref="controlbar" class="m-4" />
    <slot v-if="controlbar" :controlbar="controlbar"></slot>
  </div>
</template>
