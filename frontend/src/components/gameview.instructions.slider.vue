<script setup lang="ts">
import { ref } from "vue";
import { useGameLayout } from "@/composables/useGameLayout.ts";
import { Button } from "@/components/ui/button";

const layout = useGameLayout();
const currentStep = ref(0);
defineProps({
  num_pages: { type: Number, required: false, default: 1 },
});
const done = () => {
  layout.instructions_visible.value = false;
  setTimeout(() => {
    currentStep.value = 0;
  }, 500); // Add slight delay to allow modal to fade out
};
</script>

<template>
  <div class="grid grid-rows-[1fr_auto] justify-center w-full h-full">
    <div class="min-h-80 w-full">
      <slot class="h-full w-full" :name="'page' + (currentStep + 1)"></slot>
      <div v-if="currentStep == num_pages">
        <div class="text-lg px-10 mx-auto">
          <ul class="list-disc gap-2 h-full w-full">
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
            <li class="mt-4">
              Click the
              <Button variant="destructive" class="h-6">clear</Button>
              button reset your puzzle.
            </li>
            <li>
              Click the
              <Button variant="success" class="h-6">submit</Button>
              button to check your answer.
            </li>
            <li>
              Click the
              <Button class="h-6">new puzzle</Button>
              button for a new puzzle.
            </li>
            <li class="mb-4">
              Click the
              <Button variant="outline" class="h-6">difficulty</Button>
              dropdown to select a different size puzzle.
            </li>
          </ul>
        </div>
      </div>
    </div>
    <div class="grid grid-cols-2 w-full">
      <Button v-if="currentStep != 0" class="btn btn-outline justify-self-start" @click="currentStep--">
        Previous
      </Button>
      <Button
        v-if="currentStep < num_pages"
        class="col-start-2 btn btn-outline justify-self-end"
        @click="currentStep++"
      >
        Next
      </Button>
      <Button v-if="currentStep === num_pages" class="col-start-2 btn btn-outline justify-self-end" @click="done">
        Done!
      </Button>
    </div>
  </div>
</template>

<style scoped></style>
