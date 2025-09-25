<script setup lang="ts">
import { type PropType, ref } from "vue";
const model = defineModel();
const props = defineProps({
  min: { type: Number, default: 0 },
  max: { type: Number, default: 100 },
  modelvalue: { type: Number, default: 50 },
  step: { type: Number, default: 1 },
  labels: { type: Array as PropType<string[]>, default: () => [] },
});

// state
const slider_element = ref<HTMLInputElement>();
const half_thumb_width = 7.5; // from jsPsych CSS
function getLabelStyle(index: number): Record<string, string> | undefined {
  const label_count = props.labels.length;
  if (label_count <= 1) return undefined;

  const label_width_perc = 100 / (label_count - 1);
  const percent_of_range = index * (100 / (label_count - 1));
  const percent_dist_from_center = ((percent_of_range - 50) / 50) * 100;
  const offset = (percent_dist_from_center * half_thumb_width) / 100;

  return {
    display: "inline-block",
    position: "absolute",
    left: `calc(${percent_of_range}% - (${label_width_perc}% / 2) - ${offset}px)`,
    textAlign: "center",
    width: `${label_width_perc}%`,
    border: "1px solid transparent",
    fontSize: "80%",
  };
}
</script>

<template>
  <!-- Slider Container -->
  <div class="flex flex-col gap-2 w-full">
    <!-- Range Input -->
    <input
      ref="slider_element"
      type="range"
      class="w-full bg-transparent jspsych-slider"
      v-model="model"
      :min="min"
      :max="max"
      :step="step"
    />
    <!-- Labels -->
    <div class="relative h-5">
      <div v-for="(label, index) in labels" :key="index" class="text-sm" :style="getLabelStyle(index)" v-html="label" />
    </div>
  </div>
</template>

<style scoped>
.jspsych-slider {
  appearance: none;
  -webkit-appearance: none;
  -moz-appearance: none;
  width: 100%;
  background: transparent;
}

.jspsych-slider:focus {
  outline: none;
}

.jspsych-slider::-webkit-slider-runnable-track {
  appearance: none;
  -webkit-appearance: none;
  width: 100%;
  height: 8px;
  cursor: pointer;
  background: #eee;
  box-shadow:
    0px 0px 0px #000000,
    0px 0px 0px #0d0d0d;
  border-radius: 2px;
  border: 1px solid #aaa;
}

.jspsych-slider::-moz-range-track {
  appearance: none;
  width: 100%;
  height: 8px;
  cursor: pointer;
  background: #eee;
  box-shadow:
    0px 0px 0px #000000,
    0px 0px 0px #0d0d0d;
  border-radius: 2px;
  border: 1px solid #aaa;
}

.jspsych-slider::-ms-track {
  appearance: none;
  width: 99%;
  height: 14px;
  cursor: pointer;
  background: #eee;
  box-shadow:
    0px 0px 0px #000000,
    0px 0px 0px #0d0d0d;
  border-radius: 2px;
  border: 1px solid #aaa;
}

.jspsych-slider::-webkit-slider-thumb {
  border: 1px solid #666;
  height: 24px;
  width: 15px;
  border-radius: 5px;
  background: #ffffff;
  cursor: pointer;
  -webkit-appearance: none;
  margin-top: -9px;
}

.jspsych-slider::-moz-range-thumb {
  border: 1px solid #666;
  height: 24px;
  width: 15px;
  border-radius: 5px;
  background: #ffffff;
  cursor: pointer;
}

.jspsych-slider::-ms-thumb {
  border: 1px solid #666;
  height: 20px;
  width: 15px;
  border-radius: 5px;
  background: #ffffff;
  cursor: pointer;
  margin-top: -2px;
}
</style>
