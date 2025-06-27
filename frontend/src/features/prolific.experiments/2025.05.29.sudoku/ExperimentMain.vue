<script setup lang="ts">
import { useRoute } from "vue-router";
import { useExperimentController } from "@/features/prolific.composables/useExperimentController.ts";

const route = useRoute();
const ctrl = useExperimentController(route.meta.experiment_key as string);
</script>

<template>
  <div v-if="ctrl.is_experiment_complete.value" class="flex flex-col text-2xl gap-3 mx-auto prose flex-1 max-w-100 text-center items-center justify-around h-screen">
    <span>Thank you for participating in our experiment. If you'd like to play more games like this, please visit <a href="https://mitpuzzles.com">mitpuzzles.com</a>.</span>
  </div>
  <component
    v-else
    :is="ctrl.currentStep.value.component"
    v-bind="{
      context: ctrl,
      ...ctrl.currentStep.value.props,
    }"
  />
</template>
