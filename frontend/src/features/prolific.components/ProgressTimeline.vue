<script setup lang="ts">
import type { PropType } from "vue";
import type { useExperimentFlow } from "@/features/prolific.composables/useExperimentFlow.ts";

defineProps({
  context: {
    type: Object as PropType<ReturnType<typeof useExperimentFlow>>,
    required: true,
  },
});
</script>

<template>
  <div class="flex flex-col gap-2">
<!--    <div class="flex items-center gap-x-3 whitespace-nowrap w-full">-->
<!--      <div class="flex w-full h-2 bg-gray-200 rounded-full overflow-hidden w-full" role="progressbar" aria-valuenow="75" aria-valuemin="0" aria-valuemax="100">-->
<!--        <div class="flex flex-col justify-center rounded-full overflow-hidden bg-primary text-xs text-white text-center whitespace-nowrap transition duration-500 " style="width: 75%"></div>-->
<!--      </div>-->
<!--      <div class="w-10 text-end">-->
<!--        <span class="text-sm text-gray-800 ">75%</span>-->
<!--      </div>-->
<!--    </div>-->

    <ul class="steps border max-w-fit rounded shadow p-2">
      <li
        v-for="(step, index) in context.steps.value"
        :key="step.id"
        class="step"
        :class="{
          'step-primary': context.currentStepIndex.value >= index,
          'step-secondary!': context.currentStepIndex.value <= index,
        }"
      >
        <v-icon
          v-if="context.currentStepIndex.value === index"
          name="bi-record-circle-fill"
          scale="1.5"
          class="step-icon"
        />
        <v-icon
          v-else-if="context.currentStepIndex.value > index"
          name="bi-check-circle-fill"
          scale="1.5"
          class="step-icon"
        />
        <v-icon v-else name="bi-circle-fill" scale="1.5" class="step-icon bg-primary" />
        <div class="badge badge-primary user-select-none select-none">{{ step.label }}</div>
      </li>
    </ul>
  </div>
</template>

<style scoped></style>
