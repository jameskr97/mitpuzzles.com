<script setup lang="ts">
/**
 * DailyControlbar - Simplified control bar for daily challenge.
 * No difficulty selector, no "New Puzzle" button.
 */
import { computed, onMounted, onUnmounted } from "vue";
import type { GameController } from "@/core/games/types/game-controller";
import Container from "@/core/components/ui/Container.vue";
import { Slider } from "@/core/components/ui/slider";
import { Button } from "@/core/components/ui/button";
import { usePuzzleScaleStore } from "@/core/store/puzzle/usePuzzleScaleStore";
import { usePuzzleProgressStore } from "@/core/store/puzzle/usePuzzleProgressStore";

const props = defineProps<{
  controller: GameController;
  date: string;
}>();

const puzzle_type = props.controller.puzzle_type;
const scale_store = usePuzzleScaleStore();
const progress_store = usePuzzleProgressStore();

const current_scale = computed({
  get: () => [scale_store.getScale(puzzle_type)],
  set: (value: number[]) => scale_store.setScale(puzzle_type, value[0]),
});

const progress_key = `daily:${props.date}:${puzzle_type}`;
const formatted_time = computed(() => progress_store.get_formatted_time(progress_key));

onMounted(() => {
  function handle_keydown(e: KeyboardEvent) {
    if (e.key === "+" || e.key === "=" || e.key === "-") {
      const increment = e.key === "+" || e.key === "=" ? 5 : -5;
      e.preventDefault();
      const new_scale = Math.max(0, Math.min(100, current_scale.value[0] + increment));
      scale_store.setScale(puzzle_type, new_scale);
    }
  }
  window.addEventListener("keydown", handle_keydown);
  onUnmounted(() => window.removeEventListener("keydown", handle_keydown));
});
</script>

<template>
  <Container class="w-full md:max-w-prose mt-2 md:mt-0 mx-auto">
    <div class="flex flex-col">
      <!-- Zoom + Timer row for DESKTOP -->
      <div class="flex-row w-full items-center hidden md:flex">
        <v-icon name="co-magnifying-glass" :scale="1.5" />
        <Slider :min="0" :max="100" :step="1" class="mx-2" v-model="current_scale" />
        <span class="font-mono text-lg text-right">{{ formatted_time }}</span>
      </div>

      <!-- Timer for MOBILE -->
      <div class="flex flex-row w-full items-center md:hidden">
        <block class="font-mono text-lg text-center w-full">{{ formatted_time }}</block>
      </div>

      <!-- Buttons row (Clear + Submit only) -->
      <div class="grid grid-cols-2 w-full gap-1 mt-2">
        <Button
          variant="destructive"
          :disabled="controller.state.value.solved === true"
          @click="controller.clear_puzzle"
        >
          {{ $t("ui:action.clear") }}
        </Button>
        <Button
          variant="success"
          :disabled="controller.state.value.solved === true"
          @click="controller.check_solution"
        >
          {{ $t("ui:action.submit") }}
        </Button>
      </div>
    </div>
  </Container>
</template>
