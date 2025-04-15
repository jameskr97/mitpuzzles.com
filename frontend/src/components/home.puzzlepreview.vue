<script setup lang="ts">
import { useElementSize } from "@vueuse/core";
import { computed, ref } from "vue";
import { getUnsolvedPuzzleCount } from "@/services/app";

const props = defineProps({
  title: { type: String, required: true },
  page: { type: String, required: true },
  component: { type: Object, required: false },
  state: { type: Object, required: false },
});

const container = ref();
const puzzleRef = ref();
const { width: containerWidth } = useElementSize(container);
const scale = computed(() => {
  const totalWidth = puzzleRef.value?.totalWidth ?? 1;
  return containerWidth.value / totalWidth / 80; // 80 is an arbitrary number to make the puzzle fit nicely on the homepage
});
const count = await getUnsolvedPuzzleCount({ puzzle_type: props.page });
</script>

<template>
  <a :href="page">
    <div class="flex flex-col">
      <div ref="container" class="@container aspect-square place-items-center grid select-none pointer-events-none">
        <component :ref="puzzleRef" :is="component" :scale="scale" :state="state" class="!origin-center" />
      </div>
      <div class="divider my-0 py-0 h-full"></div>
      <div class="p-1">{{ title }} | {{ count.unsolved_count }} unsolved</div>
    </div>
  </a>
</template>
