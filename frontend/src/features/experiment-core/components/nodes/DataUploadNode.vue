<script setup lang="ts">
import { inject, onMounted, ref, type Ref } from "vue";
import { Card, CardContent } from "@/core/components/ui/card";
import { Upload, CheckCircle, AlertCircle } from "lucide-vue-next";
import type { GraphExecutor } from "@/features/experiment-core";
import { api } from "@/core/services/client";
import { capture_error } from "@/core/services/posthog.ts";

const emit = defineEmits(["complete"]);
const executor = inject<Ref<GraphExecutor>>("experiment-executor");
const status = ref<"uploading" | "completed" | "failed">("uploading");

async function start_upload() {
  if (executor?.value.data_collection) {
    try {
      executor.value.data_collection.mark_experiment_complete();
      const experiment_data = executor.value.data_collection.export_for_analysis();
      await api.POST("/api/experiment", { body: experiment_data as any });
      status.value = "completed";
      setTimeout(() => emit("complete"), 1500);
    } catch (error) {
      capture_error("experiment_upload_failed", error);
      status.value = "failed";
    }
  } else {
    capture_error("experiment_upload_failed", new Error("no experiment store available for data upload"));
    status.value = "failed";
  }
}

onMounted(() => start_upload());
</script>

<template>
  <div class="flex items-center justify-center min-h-screen bg-gray-50 p-4">
    <Card class="w-full max-w-md">
      <CardContent class="pt-6 text-center space-y-6">
        <div class="w-16 h-16 mx-auto bg-blue-100 rounded-full flex items-center justify-center">
          <Upload v-if="status === 'uploading'" class="w-8 h-8 text-blue-600 animate-spin" />
          <CheckCircle v-else-if="status === 'completed'" class="w-8 h-8 text-green-600" />
          <AlertCircle v-else class="w-8 h-8 text-red-600" />
        </div>

        <div>
          <h1 v-if="status === 'uploading'" class="text-2xl font-bold text-gray-900 mb-2">
            Uploading experiment data...
          </h1>
          <h1 v-else-if="status === 'completed'" class="text-2xl font-bold text-gray-900 mb-2">
            Experiment data received
          </h1>
          <h1 v-else class="text-2xl font-bold text-gray-900 mb-2">
            <!-- TODO(james): this should never happen, but it's not impossible. For prolific users have them message us. -->
            Upload failed.
          </h1>

          <p v-if="status === 'uploading'" class="text-sm text-gray-600">Please wait while we save your data...</p>
          <p v-else-if="status === 'completed'" class="text-sm text-gray-600">Your experiment data has been saved</p>
          <p v-else class="text-sm text-gray-600">An error occurred while saving your data</p>
        </div>
      </CardContent>
    </Card>
  </div>
</template>
