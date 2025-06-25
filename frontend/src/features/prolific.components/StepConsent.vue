<script setup lang="ts">
import { computed, defineProps, type PropType } from "vue";
import MarkdownIt from "markdown-it";
import type { ExperimentContext } from "@/features/prolific.composables/useExperimentFlow.ts";
import { markExperimentConsented } from "@/services/app.ts";
import { useCurrentExperiment } from "@/store/useCurrentExperiment.ts";
import Container from "@/components/ui/Container.vue";
import { Button } from "@/components/ui/button";

const experiment = useCurrentExperiment();

const props = defineProps({
  context: {
    type: Object as PropType<ExperimentContext>,
    required: true,
  },
  markdown: { type: String, required: true },
});

const give_consent = async () => {
  await experiment.markConsented()
  props.context.goNextStep();
};

const md = MarkdownIt({ html: true, linkify: true, typographer: true });
md.linkify.set({ fuzzyLink: false });
const html = computed(() => md.render(props.markdown));
</script>

<template>
  <div class="w-full flex-1 flex flex-col mt-2 mb-10 gap-5">
    <Container class="max-w-fit mx-auto">
      <div class="mx-auto prose flex-1" v-html="html"></div>
    </Container>
    <Button class="max-w-fit mx-auto text-xl" @click="give_consent">
      I Consent
    </Button>
  </div>
</template>
