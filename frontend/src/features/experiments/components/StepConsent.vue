<script setup lang="ts">
import { computed, onMounted, type PropType } from "vue";
import { getExperimentIdFromContext, useExperimentContent } from "@/features/experiments/core/contentLoader";
import MarkdownIt from "markdown-it";
import { Button } from "@/components/ui/button";
import Container from "@/components/ui/Container.vue";
import type { ExperimentContext } from "@/features/experiments/core/types.ts";

// Your existing props (keep these as they are)
const isDev = import.meta.env.DEV; // For development mode
const props = defineProps({
  context: { type: Object as PropType<ExperimentContext>, required: true },
  content_file: { type: String, required: true },
  requiredAgreement: { type: Boolean, default: true },
});

const emit = defineEmits(["complete", "back"]);

// REPLACE the old content loading with this:
// Get experiment ID from context or URL
const experimentId = getExperimentIdFromContext(props.context);
const { content, loading, error } = useExperimentContent(experimentId, props.content_file);

const md = MarkdownIt({ html: true, linkify: true, typographer: true });
md.linkify.set({ fuzzyLink: false });
const html = computed(() => md.render(content.value));

</script>

<template>
  <div class="w-full flex-1 flex flex-col mt-2 mb-10 gap-5">
    <Container class="max-w-fit mx-auto">
      <div class="mx-auto prose flex-1" v-html="html"></div>
    </Container>
    <Button class="max-w-fit mx-auto text-xl" @click="$emit('complete')">I Consent</Button>
  </div>


  <!--  <div class="prose">-->
  <!--    <div v-if="content" v-html="html" class="prose">-->
  <!--    </div>-->
  <!-- REPLACE your content section with this: -->
  <!--    <div class="consent-content">-->
  <!--      &lt;!&ndash; Loading state &ndash;&gt;-->
  <!--      <div v-if="isLoadingContent" class="text-center py-8">-->
  <!--        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>-->
  <!--        <p class="text-gray-600">Loading consent form...</p>-->
  <!--      </div>-->

  <!--      &lt;!&ndash; Error state (shows fallback content) &ndash;&gt;-->
  <!--      <div v-else-if="contentError" class="text-center py-8 mb-4">-->
  <!--        <div class="text-yellow-600 mb-2">-->
  <!--          <svg class="w-6 h-6 mx-auto" fill="currentColor" viewBox="0 0 20 20">-->
  <!--            <path-->
  <!--              fill-rule="evenodd"-->
  <!--              d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"-->
  <!--              clip-rule="evenodd"-->
  <!--            />-->
  <!--          </svg>-->
  <!--        </div>-->
  <!--        <p class="text-sm text-gray-600">Could not load consent file. Using default content.</p>-->
  <!--      </div>-->

  <!-- Content display -->

  <!--    </div>-->

  <!-- Keep your existing navigation section as-is -->
  <!--    <div class="consent-navigation mt-8 flex justify-between items-center">-->
  <!--      <button @click="$emit('back')" class="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors">-->
  <!--        Back-->
  <!--      </button>-->

  <!--      <div class="flex space-x-3">-->
  <!--        <button @click="handleAgree">I Agree & Continue</button>-->
  <!--      </div>-->
  <!--    </div>-->

  <!-- Optional: Debug info for development -->
  <!--    <div v-if="isDev" class="mt-8 p-4 bg-yellow-50 border border-yellow-200 rounded text-xs">-->
  <!--      <strong>Debug Info:</strong><br />-->
  <!--      Experiment ID: {{ experimentId }}<br />-->
  <!--      Content File: {{ contentFile || "None" }}<br />-->
  <!--      Content Loading: {{ isLoadingContent }}<br />-->
  <!--      Content Error: {{ contentError || "None" }}<br />-->
  <!--    </div>-->
  <!--  </div>-->
</template>

<style scoped>
/* Keep your existing styles */
.consent-step {
  padding: 2rem 1rem;
}

.consent-content {
  min-height: 400px;
}

/* Keep your existing mobile styles */
@media (max-width: 768px) {
  .consent-step {
    padding: 1rem 0.5rem;
  }

  .consent-navigation {
    flex-direction: column;
    gap: 1rem;
  }

  .consent-navigation > div {
    order: -1;
  }
}
</style>
