<script setup lang="ts">
import GameTimer from "@/components/ui/game/game.timer.vue";
import { remap } from "@/lib/util";
import { ref, computed } from "vue";

const scale = ref(30);
const scale_remapped = computed(() => remap([0, 100], [2, 6], scale.value)); 
</script>

<template>
  <div class="flex flex-col">
    <div class="col-span-3 border-0 border-red-500 mx-auto">
      <slot name="left"></slot>
    </div>

    <div class="w-full md:w-2/3 mx-auto p-2">
      <div class="h-full flex flex-col">
        <!-- GAME CONTROL BAR -->
        <div class="flex flex-col">
          <div class="flex flex-row items-center justify-around gap-2 px-2">
            <div
              class="tooltip tooltip-bottom w-full"
              data-tip="Resize Game Board"
            >
              <input
                v-model="scale"
                type="range"
                min="0"
                max="100"
                class="range w-full"
              />
            </div>

            <!-- SEPARATOR -->
            <div class="divider divider-horizontal px-0 mx-0"></div>

            <!-- REDO + UNDO Buttons -->
            <div class="tooltip tooltip-bottom" data-tip="Undo Last Action">
              <v-icon class="ms-auto" name="fa-undo-alt" scale="1.5" />
            </div>
            <div class="tooltip tooltip-bottom" data-tip="Redo Last Action">
              <v-icon name="fa-redo-alt" scale="1.5" />
            </div>

            <!-- SEPARATOR -->
            <div class="divider divider-horizontal px-0 mx-0"></div>
            <!-- <GameTimer
              class="font-mono"
              v-if="store.puzzle"
              :time-received="store.puzzle.received_at"
              :time-completed="store.puzzle.completed_at"
            /> -->
          </div>
        </div>

        <div class="divider divider-vertical my-1"></div>

        <!-- Game Content -->
        <div class="grid grid-cols-1 place-items-center">
          <slot name="default" :scale="scale_remapped"></slot>
        </div>
      </div>
    </div>

    <div class="col-span-3 border-0 border-green-500">
      <slot name="right"></slot>
    </div>
  </div>
</template>
