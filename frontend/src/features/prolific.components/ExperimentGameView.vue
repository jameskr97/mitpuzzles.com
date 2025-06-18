<script setup lang="ts">
import { remap } from "@/services/util.ts";
import { ref, watch } from "vue";

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
  <div class="mx-auto p-2 flex-col">
    <div class="flex flex-col items-center w-full md:w-3/5 2xl:w-2/4 mx-auto justify-around gap-2 px-2">

      <div class="flex flex-row w-full gap-4">
        <div class="text-nowrap">Resize Bar</div>
        <div class="tooltip tooltip-bottom w-full" data-tip="Resize Game Board">
        <input type="range" min="0" max="100" class="range w-full user-select-none" v-model="scale" />
      </div>
      </div>
      <div class="flex flex-row mt-2 w-full">
        <button class="btn btn-primary w-full" @click="emit('gameSubmitted')">Submit</button>
      </div>
      <div class="grow">
        <slot></slot>
      </div>

    </div>
  </div>
</template>
