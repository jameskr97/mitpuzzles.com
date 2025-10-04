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
    <div class="h-140 w-full">
      <slot class="h-full" :name="'page' + (currentStep + 1)"></slot>
      <div v-if="currentStep == num_pages">
        <div class="text-lg mx-auto flex flex-col gap-4">
          <div>
            <div class="font-bold">Game Controls</div>
            <slot name="controls"></slot>
            <div>Click <span class="text-green-600">submit</span> when you think you have solved the puzzle.</div>
          </div>
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
