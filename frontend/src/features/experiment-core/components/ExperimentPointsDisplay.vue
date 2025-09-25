<script setup lang="ts">
import { computed, inject, reactive, watch } from "vue";
import type { Ref } from "vue";
import { gsap } from "gsap";
import Container from "@/components/ui/Container.vue";
import { GraphExecutor } from "@/features/experiment-core";

// props + inject
const executor = inject<Ref<GraphExecutor>>("experiment-executor");
withDefaults(defineProps<{ label_text?: string }>(), { label_text: "points" });

// state
const tweened = reactive({ number: 0 });
const current_points = computed(() => executor?.value.data_collection.total_points);

//  watch for point changes
watch(current_points, (new_points) => {
  gsap.to(tweened, {
    duration: 2,
    number: new_points,
    ease: "power2.out",
  });
});
</script>

<template>
  <Container
    class="points-display flex flex-col items-center text-center max-w-fit mx-auto transition-all duration-200 text-2xl p-2"
  >
    {{ tweened.number.toFixed(0) }} {{ label_text }}
  </Container>
</template>
