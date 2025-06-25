<script setup lang="ts">
import {
  Stepper,
  StepperIndicator,
  StepperItem,
  StepperSeparator,
  StepperTitle,
  StepperTrigger,
} from "@/components/ui/stepper";
import type { PropType } from "vue";
import type { useExperimentFlow } from "@/features/prolific.composables/useExperimentFlow.ts";
import Container from "@/components/ui/Container.vue";

defineProps({
  context: {
    type: Object as PropType<ReturnType<typeof useExperimentFlow>>,
    required: true,
  },
});
</script>

<template>
  <Container class="max-w-prose">
    <Stepper v-model="context.currentStepIndex" :steps="context.steps">
      <StepperItem v-for="(step, index) in context.steps.value" :key="step.id" :step="index">
        <StepperTrigger>
          <StepperIndicator>{{ index + 1 }}</StepperIndicator>
          <StepperTitle>{{ step.label }}</StepperTitle>
        </StepperTrigger>
        <StepperSeparator />
      </StepperItem>
    </Stepper>
  </Container>

  <!--  <div class="flex flex-col gap-2">-->
  <!--    <ul class="steps border max-w-fit rounded shadow p-2">-->
  <!--      <li-->
  <!--        v-for="(step, index) in context.steps.value"-->
  <!--        :key="step.id"-->
  <!--        class="step"-->
  <!--        :class="{-->
  <!--          'step-primary': context.currentStepIndex.value >= index,-->
  <!--          'step-secondary!': context.currentStepIndex.value <= index,-->
  <!--        }"-->
  <!--      >-->
  <!--        <v-icon-->
  <!--          v-if="context.currentStepIndex.value === index"-->
  <!--          name="bi-record-circle-fill"-->
  <!--          scale="1.5"-->
  <!--          class="step-icon"-->
  <!--        />-->
  <!--        <v-icon-->
  <!--          v-else-if="context.currentStepIndex.value > index"-->
  <!--          name="bi-check-circle-fill"-->
  <!--          scale="1.5"-->
  <!--          class="step-icon"-->
  <!--        />-->
  <!--        <v-icon v-else name="bi-circle-fill" scale="1.5" class="step-icon bg-primary" />-->
  <!--        <div class="badge badge-primary user-select-none select-none">{{ step.label }}</div>-->
  <!--      </li>-->
  <!--    </ul>-->
  <!--  </div>-->
</template>

<style scoped></style>
