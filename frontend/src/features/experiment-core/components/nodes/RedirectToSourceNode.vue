<script setup lang="ts">
import { computed, inject, onMounted, onUnmounted, ref, type Ref } from "vue";
import { Card, CardContent } from "@/core/components/ui/card";
import { Button } from "@/core/components/ui/button";
import { CheckCircle, Copy } from "lucide-vue-next";
import type { prolific_redirect_meta } from "@/features/experiment-core/graph/types";
import type { GraphExecutor } from "@/features/experiment-core";

// configuraiton
const executor = inject<Ref<GraphExecutor>>("experiment-executor");
const config = computed<prolific_redirect_meta>(() => executor?.value.current_node?.config.meta);
const completion_code = computed(() => config.value.completion_code);

// state
const countdown = ref(3);
const redirect_failed = ref(false);
const timer_id = ref<number | null>(null);
const copied = ref(false);

// functions
const recruitment_platform = computed(() => executor?.value.data_collection.participant_data?.recruitment_platform);
const manual_redirect = () => (window.location.href = redirect_url.value);
const redirect_url = computed(() => {
  const platform = recruitment_platform.value;
  if (platform === "prolific") {
    return `https://app.prolific.com/submissions/complete?cc=${completion_code.value}`;
  } else {
    return "/";
  }
});

async function copy_code() {
  try {
    await navigator.clipboard.writeText(completion_code.value);
    copied.value = true;
    setTimeout(() => (copied.value = false), 2000);
  } catch (err) {
    console.error("Failed to copy:", err);
  }
}

// auto redirect with countdown
function start_redirect_countdown() {
  const do_countdown = () => {
    countdown.value--;

    if (countdown.value <= 0) {
      if (timer_id.value) {
        clearInterval(timer_id.value);
        timer_id.value = null;
      }

      // attempt redirect
      try {
        window.location.href = redirect_url.value;
      } catch (err) {
        console.error("redirect failed:", err);
        redirect_failed.value = true;
      }
    }
  };
  timer_id.value = window.setInterval(() => do_countdown(), 1000);
}

// cleanup
function cleanup_timer() {
  if (timer_id.value) {
    clearInterval(timer_id.value);
    timer_id.value = null;
  }
}

onMounted(() => start_redirect_countdown());
onUnmounted(() => cleanup_timer());
</script>

<template>
  <div class="flex items-center justify-center min-h-screen bg-gray-50 p-4">
    <Card class="w-full max-w-md">
      <CardContent class="pt-6 text-center space-y-6">
        <div class="w-16 h-16 mx-auto bg-green-100 rounded-full flex items-center justify-center">
          <CheckCircle class="w-8 h-8 text-green-600" />
        </div>

        <div>
          <h1 class="text-2xl font-bold text-gray-900 mb-2">Experiment Complete!</h1>
          <p class="text-sm text-gray-600">Thank you for participating</p>
        </div>

        <div v-if="recruitment_platform === 'prolific'" class="space-y-3">
          <p class="text-sm text-gray-600">Your completion code is:</p>
          <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <code class="text-2xl font-mono font-bold text-blue-600 tracking-wider">
              {{ completion_code }}
            </code>
          </div>
          <Button @click="copy_code" variant="outline" size="sm" class="w-full">
            <Copy class="w-4 h-4 mr-2" />
            {{ copied ? "Copied!" : "Copy code" }}
          </Button>
        </div>

        <div class="space-y-3">
          <div class="text-sm text-gray-600">
            <span v-if="!redirect_failed && recruitment_platform === 'prolific'">
              Redirecting to prolific in {{ countdown }}s...
            </span>
            <span v-else-if="!redirect_failed && recruitment_platform === 'direct'">
              Redirecting to home page in {{ countdown }}s...
            </span>
            <div v-else>
              <p>Automatic redirect failed</p>
              <p>Please use the button below:</p>
              <Button variant="blue" class="mt-2" @click="manual_redirect">
                {{ recruitment_platform === "prolific" ? "Return to prolific" : "Return to home page" }}
              </Button>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  </div>
</template>
