<script setup lang="ts">
import type { ReturnType } from "@/features/prolific.composables/useExperimentFlow";

defineProps({
  context: {
    type: Object as PropType<ReturnType>,
    required: true,
  },
});
</script>

<template>
  <div class="flex h-dvh overflow-y-auto">
    <div class="grow grid grid-rows-[1fr_auto] min-h-full mt-2">
      <div class="grow">
        <component :is="context.currentStep.value.component" v-bind="context.currentStep.value.props" />
      </div>
      <footer
        class="footer flex justify-between w-full sm:footer-horizontal footer-center text-base-content p-2 sticky bg-base-100 bottom-0 border-t-2"
      >
        <button
          class="btn btn-secondary h-full"
          @click="context.goPreviousStep()"
          @mousedown.prevent
          :class="{ invisible: context.currentStepIndex.value === 0 }"
        >
          Previous
        </button>
        <div>
          <slot name="timeline" />
        </div>
        <button class="btn btn-primary h-full" tabindex="-1" @click="context.goNextStep()" @mousedown.prevent>
          Continue
        </button>
      </footer>
    </div>
  </div>
</template>
