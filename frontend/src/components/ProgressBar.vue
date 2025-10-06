<script setup lang="ts">
import Container from "@/components/ui/Container.vue";

defineProps({
  current_step: { type: Number, default: 0 },
  segments: { type: Number, default: 5 },
  container_class: { type: String, default: "" },
  active_class: { type: String, default: "bg-gray-600" },
  inactive_class: { type: String, default: "bg-gray-300" },
  show_numerical_progress: { type: Boolean, default: false },
});
</script>

<template>
  <Container
    class="min-w-fit md:w-full md:max-w-prose md:mx-auto h-8 m-2 mt-0 rounded-full! overflow-clip border-1 p-1! flex flex-row justify-between gap-1"
    :key="current_step"
  >
    <div
      v-for="(_, index) in segments"
      :key="index"
      :class="[
        current_step > index ? active_class : inactive_class,
        {
          'rounded-l-full': index === 0,
          'rounded-r-full': index === segments - 1,
        },
      ]"
      class="h-full w-full"
    ></div>
    <div v-if="show_numerical_progress" class="min-w-fit ml-1 mr-2 text-xl leading-5 mt-0.5">
      {{ current_step }} of {{ segments }}
    </div>
  </Container>
</template>
