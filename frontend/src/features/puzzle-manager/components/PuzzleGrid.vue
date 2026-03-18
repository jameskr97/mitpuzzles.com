<script setup lang="ts">
import { ref, watch } from "vue";
import { ChevronLeft, ChevronRight } from "lucide-vue-next";
import { api } from "@/core/services/client";

import { Badge } from "@/core/components/ui/badge";
import { Button } from "@/core/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/core/components/ui/select";
import PuzzleRenderer from "@/core/components/PuzzleRenderer.vue";
import type { BackgroundJob, AnalysisJobPuzzle, PaginatedPuzzles } from "../types";
import { get_result_variant, convert_to_definition } from "../utils";

const props = defineProps<{
  job: BackgroundJob;
}>();

const emit = defineEmits<{
  "select-puzzle": [puzzle: AnalysisJobPuzzle];
}>();

const puzzles = ref<PaginatedPuzzles | null>(null);
const loading = ref(false);
const page = ref(1);
const result_filter = ref<string | undefined>(undefined);

const fetch_puzzles = async () => {
  try {
    loading.value = true;
    const query: Record<string, any> = { page: page.value, page_size: 20 };
    if (result_filter.value && result_filter.value !== "null") {
      query.result_filter = result_filter.value;
    }
    const { data } = await api.GET("/api/analysis/jobs/{job_id}/puzzles", {
      params: { path: { job_id: props.job.id }, query },
    });
    if (data) puzzles.value = data as any;
  } catch (err) {
    console.error("Error fetching puzzles:", err);
  } finally {
    loading.value = false;
  }
};

watch([page, result_filter], () => {
  fetch_puzzles();
});

watch(
  () => props.job.id,
  () => {
    page.value = 1;
    result_filter.value = undefined;
    fetch_puzzles();
  },
  { immediate: true },
);
</script>

<template>
  <div>
    <!-- Filter -->
    <div class="flex items-center gap-4 mb-4">
      <span class="text-sm text-muted-foreground">Filter by result:</span>
      <Select v-model="result_filter">
        <SelectTrigger class="w-[180px]">
          <SelectValue placeholder="All results" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="null">All results</SelectItem>
          <SelectItem value="unique">Unique</SelectItem>
          <SelectItem value="invalid">Invalid</SelectItem>
          <SelectItem value="multi_solution">Multi-solution</SelectItem>
          <SelectItem value="duplicate">Duplicate</SelectItem>
          <SelectItem value="error">Error</SelectItem>
        </SelectContent>
      </Select>
    </div>

    <!-- Grid -->
    <div v-if="loading" class="text-center py-8 text-muted-foreground">Loading puzzles...</div>
    <div v-else-if="puzzles">
      <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
        <div
          v-for="puzzle in puzzles.items"
          :key="puzzle.id"
          class="border rounded-lg p-3 cursor-pointer hover:border-primary transition-colors"
          @click="emit('select-puzzle', puzzle)"
        >
          <div class="flex items-center justify-between mb-2">
            <span class="text-xs text-muted-foreground">#{{ puzzle.puzzle_index }}</span>
            <Badge :variant="get_result_variant(puzzle.result)" class="text-xs">
              {{ puzzle.result || puzzle.status }}
            </Badge>
          </div>
          <div class="flex justify-center">
            <PuzzleRenderer :show_solution="true" :definition="convert_to_definition(puzzle.puzzle_data)" />
          </div>
          <div
            v-if="puzzle.solution_count && puzzle.solution_count > 1"
            class="text-center text-xs text-muted-foreground mt-2"
          >
            {{ puzzle.solution_count }} solutions
          </div>
          <div
            v-if="puzzle.error_message"
            class="text-center text-xs text-red-500 mt-2 truncate"
            :title="puzzle.error_message"
          >
            {{ puzzle.error_message }}
          </div>
        </div>
      </div>

      <!-- Pagination -->
      <div class="flex items-center justify-between mt-4 pt-4 border-t">
        <div class="text-sm text-muted-foreground">
          Showing {{ (puzzles.page - 1) * puzzles.page_size + 1 }} -
          {{ Math.min(puzzles.page * puzzles.page_size, puzzles.total) }} of {{ puzzles.total }}
        </div>
        <div class="flex gap-2">
          <Button variant="outline" size="sm" :disabled="puzzles.page <= 1" @click="page--">
            <ChevronLeft class="h-4 w-4" />
            Previous
          </Button>
          <Button variant="outline" size="sm" :disabled="puzzles.page >= puzzles.total_pages" @click="page++">
            Next
            <ChevronRight class="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  </div>
</template>
