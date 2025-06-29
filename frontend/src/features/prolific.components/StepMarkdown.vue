<script setup lang="ts">
import { computed, defineProps, type PropType } from "vue";
import MarkdownIt from "markdown-it";
import type { ExperimentContext } from "@/features/prolific.composables/useExperimentFlow.ts";

const props = defineProps({
  context: {
    type: Object as PropType<ExperimentContext>,
    required: true,
  },
  markdown: { type: String, required: true },
  buttonText: { type: String, default: "Submit" },
});

const md = MarkdownIt({ html: true, linkify: true, typographer: true });
md.linkify.set({ fuzzyLink: false });
const html = computed(() => md.render(props.markdown));
</script>

<template>
  <div class="w-full flex-1 flex flex-col">
    <div class="mx-auto prose flex-1" v-html="html"></div>
    <button type="button" class="btn btn-lg btn-primary mt-3 mb-6 mx-auto" @click="context.goNextStep()">
      {{ buttonText }}
    </button>
  </div>
</template>
