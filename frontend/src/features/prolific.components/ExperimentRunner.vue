<script setup lang="ts">

const {
  currentStep,
  steps,
  currentStepIndex,
  goNextStep,
  percentageCompleted,
} = useExperimentFlow();
</script>

<template>
  <div class="flex h-dvh overflow-y-auto">
    <div class="grow grid grid-rows-[1fr_auto] min-h-full mt-2">
      <component
        :is="currentStep"
        v-bind="{
          ...(currentStep.props || {}),
          context: { goNextStep }
        }"
      />
      <footer
        class="footer flex justify-between w-full sm:footer-horizontal footer-center text-base-content p-2 sticky bg-base-100 bottom-0 border-t-2 bg-white"
      >
        <div class="mx-auto">
        </div>
      </footer>
    </div>
  </div>
</template>
