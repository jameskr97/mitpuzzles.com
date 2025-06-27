<script setup lang="ts">
import { remap } from "@/services/util.ts";
import ExperimentViewControlBar from "@/components/experimentview.controlbar.vue";
import { ref, watch } from "vue";
import ExperimentViewPointCounter from "@/components/experimentview.pointcounter.vue";

const emit = defineEmits(["scaleChange", "gameSubmitted"]);
const scale = ref(80);
watch(
  scale,
  (newScale) => {
    emit("scaleChange", remap([1, 100], [1, 5], newScale));
  },
  { immediate: true },
);
</script>

<template>
  <div class="mx-auto p-2 flex-col w-full">
    <div class="flex flex-col items-center w-full mx-auto justify-around gap-2 px-2">
      <div class="flex flex-col w-full gap-4">
        <ExperimentViewControlBar @submit-click="emit('gameSubmitted')" />
        <ExperimentViewPointCounter class="mx-auto" />
      </div>
      <div class="grow">
        <slot></slot>
      </div>
    </div>
  </div>
</template>
