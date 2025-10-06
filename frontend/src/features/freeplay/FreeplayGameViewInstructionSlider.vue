<script setup lang="ts">
import { ref, onMounted, onUnmounted } from "vue";
import { useGameLayout } from "@/composables/useGameLayout.ts";
import { Button } from "@/components/ui/button";
import ProgressBar from "@/components/ProgressBar.vue";
import FreeplayGameViewInstructionPage from "./FreeplayGameViewInstructionPage.vue";

const layout = useGameLayout();
const currentStep = ref(0);
const props = defineProps({
  num_pages: { type: Number, required: false, default: 1 },
});

const go_previous = () => {
  if (currentStep.value > 0) {
    currentStep.value--;
  }
};

const go_next = () => {
  if (currentStep.value < props.num_pages) {
    currentStep.value++;
  } else if (currentStep.value === props.num_pages) {
    done();
  }
};

const done = () => {
  layout.instructions_visible.value = false;
  setTimeout(() => {
    currentStep.value = 0;
  }, 500); // Add slight delay to allow modal to fade out
};

const handle_keydown = (event: KeyboardEvent) => {
  if (event.key === "ArrowLeft") {
    event.preventDefault();
    go_previous();
  } else if (event.key === "ArrowRight") {
    event.preventDefault();
    go_next();
  }
};

onMounted(() => {
  window.addEventListener("keydown", handle_keydown);
});

onUnmounted(() => {
  window.removeEventListener("keydown", handle_keydown);
});
</script>

<template>
  <div class="grid grid-rows-[1fr_auto] justify-center w-full h-full">
    <!-- Content Area with Scroll -->
    <div class="overflow-y-auto min-h-0 px-4">
      <slot v-if="currentStep < num_pages" class="h-full" :name="'page' + (currentStep + 1)"></slot>
      <FreeplayGameViewInstructionPage layout_mode="content-only" v-else>
        <template #instruction>
          <div class="text-lg flex flex-col gap-4">
            <div>
              <div class="font-bold">Game Controls</div>
              <slot name="controls"></slot>
              <div>Click <span class="text-green-600">submit</span> when you think you have solved the puzzle.</div>
            </div>
          </div>
        </template>

        <template #board>
          <div>
              <div class="font-bold">Misc Information</div>
              <ul class="gap-2 h-full w-full">
                <li>
                  You can click in the information circle
                  <v-icon name="hi-information-circle" :scale="1.5" class="cursor-pointer" />
                  to review these rules.
                </li>

                <li>
                  You can click on the settings gear
                  <v-icon name="io-settings-outline" :scale="1.5" class="cursor-pointer" />
                  to turn on tutorial mode. Tutorial mode will show you any game rules you break while trying to solve the
                  puzzle.
                </li>
              </ul>
            </div>
        </template>
      </FreeplayGameViewInstructionPage>
    </div>

    <!-- Fixed Button Footer with Progress Bar -->
    <div class="grid grid-cols-[auto_1fr_auto] items-center gap-4 w-full px-4 py-2">
      <Button
        class="btn btn-outline"
        :disabled="currentStep === 0"
        @click="go_previous"
      >
        <kbd class="kbd kbd-sm">←</kbd>
      </Button>

      <!-- Progress Bar in Center -->
      <ProgressBar
        :current_step="currentStep + 1"
        :segments="num_pages + 1"
        container_class="mx-2"
      />

      <Button class="btn btn-outline" @click="go_next">
        <kbd class="kbd kbd-sm">→</kbd>
      </Button>

    </div>
  </div>
</template>

<style scoped></style>
