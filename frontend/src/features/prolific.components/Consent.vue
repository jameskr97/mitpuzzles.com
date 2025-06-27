<script setup lang="ts">
import { computed, defineProps } from "vue";
import MarkdownIt from "markdown-it";
import Container from "@/components/ui/Container.vue";
import { Button } from "@/components/ui/button";
import { useGameService } from "@/services/game/useGameService.ts";
import type { WebsocketGameService } from "@/services/game/WebsocketGameService.ts";
import { useExperimentController } from "@/features/prolific.composables/useExperimentController.ts";
import { useRoute } from "vue-router";

const route = useRoute();
const ec = useExperimentController(route.meta.experiment_key as string);
const props = defineProps({
  markdown: { type: String, required: true },
});


const md = MarkdownIt({ html: true, linkify: true, typographer: true });
md.linkify.set({ fuzzyLink: false });
const html = computed(() => md.render(props.markdown));
</script>

<template>
  <div class="w-full flex-1 flex flex-col mt-2 mb-10 gap-5">
    <Container class="max-w-fit mx-auto">
      <div class="mx-auto prose flex-1" v-html="html"></div>
    </Container>
    <Button class="max-w-fit mx-auto text-xl" @click="ec.consent"> I Consent </Button>
  </div>
</template>
