<script setup lang="ts">
import { Download, Ban } from "lucide-vue-next";
import axios from "axios";

import { Badge } from "@/core/components/ui/badge";
import { Button } from "@/core/components/ui/button";
import type { BackgroundJob } from "../types";
import { format_date, get_status_variant } from "../utils";

const props = defineProps<{
  job: BackgroundJob;
}>();

const emit = defineEmits<{
  refresh: [];
}>();

const import_unique = async () => {
  try {
    const response = await axios.post(`/api/analysis/jobs/${props.job.id}/import-unique`);
    alert(`Imported ${response.data.imported} unique puzzles`);
    emit("refresh");
  } catch (err: any) {
    console.error("Error importing puzzles:", err);
    alert(err.response?.data?.detail || "Failed to import puzzles");
  }
};

const disable_non_unique = async () => {
  if (!confirm("This will disable (set is_active=false) all multi-solution puzzles found. Continue?")) {
    return;
  }

  try {
    const response = await axios.post(`/api/analysis/jobs/${props.job.id}/disable-non-unique`);
    alert(`Disabled ${response.data.disabled} non-unique puzzles`);
    emit("refresh");
  } catch (err: any) {
    console.error("Error disabling puzzles:", err);
    alert(err.response?.data?.detail || "Failed to disable puzzles");
  }
};
</script>

<template>
  <div class="bg-muted/30 rounded-lg p-4">
    <div class="flex items-center justify-between mb-2">
      <div class="text-lg font-semibold">{{ job.source_filename || "Untitled Job" }}</div>
      <Badge :variant="get_status_variant(job.status)">{{ job.status }}</Badge>
    </div>

    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
      <div>
        <span class="text-muted-foreground">Type:</span>
        <span class="ml-1 font-medium">{{ job.puzzle_type }}</span>
      </div>
      <div>
        <span class="text-muted-foreground">Total:</span>
        <span class="ml-1 font-medium">{{ job.total_puzzles }}</span>
      </div>
      <div>
        <span class="text-muted-foreground">Created:</span>
        <span class="ml-1">{{ format_date(job.created_at) }}</span>
      </div>
      <div v-if="job.completed_at">
        <span class="text-muted-foreground">Completed:</span>
        <span class="ml-1">{{ format_date(job.completed_at) }}</span>
      </div>
    </div>

    <div class="flex gap-2 mt-3 flex-wrap">
      <Badge variant="green">{{ job.unique_count }} unique</Badge>
      <Badge variant="red">{{ job.invalid_count }} invalid</Badge>
      <Badge variant="secondary">{{ job.multi_solution_count }} multi-solution</Badge>
      <Badge variant="secondary" v-if="job.duplicate_count > 0">{{ job.duplicate_count }} duplicate</Badge>
      <Badge variant="red" v-if="job.error_count > 0">{{ job.error_count }} errors</Badge>
    </div>

    <!-- Action Buttons -->
    <div v-if="job.status === 'completed'" class="flex gap-2 mt-4 pt-4 border-t">
      <Button v-if="job.unique_count > 0" variant="default" size="sm" @click="import_unique">
        <Download class="h-4 w-4 mr-2" />
        Import All Unique ({{ job.unique_count }})
      </Button>
      <Button
        v-if="job.multi_solution_count > 0 && job.job_type === 'database_audit'"
        variant="destructive"
        size="sm"
        @click="disable_non_unique"
      >
        <Ban class="h-4 w-4 mr-2" />
        Disable Non-Unique in DB ({{ job.multi_solution_count }})
      </Button>
    </div>
  </div>
</template>
