<script setup lang="ts">
import { ref } from "vue";
import Container from "@/components/ui/Container.vue";

const props = defineProps({
  title: { type: String, required: true },
  page: { type: String, required: true },
  component: { type: Object, required: false },
  state: { type: Object, required: false },
});

const container = ref();
const puzzleRef = ref();
</script>

<template>
  <router-link :to="{ name: 'game-' + page }">
    <Container class="overflow-hidden hover:-translate-y-0.5 transition-all duration-200 mb-0 pb-0">
      <div class="flex flex-col gap-1">
        <div class="overflow-hidden min-w-0">
          <div
            ref="container"
            class="@container aspect-square box-border place-items-center grid select-none pointer-events-none rounded-xs overflow-hidden"
          >
            <component :ref="puzzleRef" :is="component" :state="state" :parentEl="container" />
          </div>
        </div>
      </div>
      <div class="text-center mt-1">{{ props.title }}</div>
    </Container>
  </router-link>
</template>
