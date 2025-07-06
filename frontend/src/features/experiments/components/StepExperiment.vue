<script setup lang="ts">
import { computed, type PropType } from "vue";
import type { ExperimentContext, ExperimentStep } from "@/features/experiments/core/types.ts";
import { Button } from "@/components/ui/button";
import Container from "@/components/ui/Container.vue";

// Props
const props = defineProps({
  step: { type: Object as PropType<ExperimentStep>, required: true },
  component: { type: [Object, Function], required: true },
  context: { type: Object as PropType<ExperimentContext>, required: true },
});

// Events
const emit = defineEmits<{
  complete: [data?: any];
  back: [];
  skip: [];
}>();

// Merge step props with context
const componentProps = computed(() => ({
  context: props.context,
  ...props.step.props,
}));

// Navigation helpers
const nextButtonText = computed(() => props.context?.stepData?.nextButtonText || "Continue");
const canGoBack = computed(() => props.context.currentStep > 0);
const canSkip = computed(() => {
  // Allow skipping based on step configuration or experiment settings
  return props.step.type !== "consent"; // Example: can't skip consent
});

// Handle step events
function handleComplete(data?: any) {
  emit("complete", data);
}

function handleBack() {
  if (canGoBack.value) {
    emit("back");
  }
}

function handleSkip() {
  if (canSkip.value) {
    emit("skip");
  }
}

// Provide navigation methods to child component
function injectNavigationMethods() {
  return {
    complete: handleComplete,
    back: handleBack,
    skip: handleSkip,
    canGoBack: canGoBack.value,
    canSkip: canSkip.value,
  };
}
</script>

<template>
  <div class="experiment-step" :data-step-type="step.type" :data-step-id="step.id">
    <!-- Step container with proper spacing and scrolling -->
    <div class="step-content">
      <component
        :is="component"
        v-bind="componentProps"
        @complete="handleComplete"
        @back="handleBack"
        @skip="handleSkip"
      />
    </div>

  </div>
</template>

<style scoped>
.experiment-step {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.step-content {
  flex: 1;
  overflow: auto;
  padding: 2rem 1.5rem;
}


/* Different layouts for different step types */
.experiment-step[data-step-type="puzzle-trial"] .step-content {
  padding: 1rem;
  display: flex;
  flex-direction: column;
}

.experiment-step[data-step-type="consent"] .step-content,
.experiment-step[data-step-type="instructions"] .step-content {
  max-width: 4xl;
  margin: 0 auto;
}

.experiment-step[data-step-type="survey"] .step-content {
  max-width: 2xl;
  margin: 0 auto;
}

</style>
