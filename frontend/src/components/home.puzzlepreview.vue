<script setup lang="ts">
import { ref } from "vue";
import Container from "@/components/ui/Container.vue";
import { TooltipTrigger, Tooltip, TooltipContent } from "@/components/ui/tooltip";

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
  <Tooltip>
    <TooltipTrigger>
      <Container class="overflow-hidden">
        <router-link :to="{ name: 'game-' + page }">
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
        </router-link>
      </Container>
    </TooltipTrigger>
    <!-- suppress RequiredAttributes -->
    <TooltipContent side="bottom">
      <div class="text-center text-2xl">{{ props.title }}</div>
    </TooltipContent>
  </Tooltip>
</template>
