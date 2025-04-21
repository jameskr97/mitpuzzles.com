<script setup lang="ts">
import logger from "@/services/logger.ts";
import { computed, ref } from "vue";
import { submitFeedback } from "@/services/app.ts";
import { getPuzzle } from "@/composables/useCurrentPuzzle.ts";
import { useRoute } from "vue-router";

// Interfaces
interface Metadata {
  url: string;
  puzzle_id?: number;
}

// Constants
const btnSubmitText = computed(() => (submitting.value ? "Submitting..." : "Send Feedback"));
const btnOpenFeedback = computed(() => (submitted.value ? "Thank you!" : "Send us Feedback!"));

// References
const submitted = ref(false);
const submitting = ref(false);
const feedback = ref("");
const is_open = ref(false);
const route = useRoute();

async function submit() {
  const p = await getPuzzle(route.meta.game_type as string).catch(() => undefined);
  const metadata: Metadata = { url: window.location.pathname };
  if (p) metadata.puzzle_id = p.puzzle_id;

  submitting.value = true;
  try {
    const res = await submitFeedback(feedback.value, metadata);
    if (res.status !== 201) logger.error("Failed to submit feedback", res);

    feedback.value = "";
    is_open.value = false;
    submitted.value = true;
    setTimeout(() => (submitted.value = false), 3000);
    logger.info("Feedback submitted successfully");
  } catch (e: any) {
    logger.error("Failed to submit feedback", e);
  } finally {
    submitting.value = false;
  }
}
</script>

<template>
  <details class="dropdown dropdown-top mx-auto w-full" :open="is_open">
    <summary class="btn btn-secondary w-full" @click.prevent="is_open = !is_open">{{ btnOpenFeedback }}</summary>
    <div
      tabindex="0"
      class="dropdown-content card mb-1 bg-base-100 z-50 w-full h-100 shadow-md border-2 border-black"
    >
      <p>Thanks for trying our website. Did you like it? Did something not work right! Let us know here!</p>
      <textarea
        class="textarea textarea-md resize-none h-full w-full my-2"
        placeholder="Share your thoughts here!"
        v-model="feedback"
        :disabled="submitting"
      ></textarea>
      <button tabindex="0" class="btn btn-primary" @click="submit" :disabled="submitting">{{ btnSubmitText }}</button>
    </div>
  </details>
</template>
