<script setup lang="ts">
import { Badge } from "@/core/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/core/components/ui/dialog";
import PuzzleRenderer from "@/core/components/PuzzleRenderer.vue";
import type { AnalysisJobPuzzle } from "../types";
import { get_result_variant, convert_to_definition } from "../utils";

const props = defineProps<{
  puzzle: AnalysisJobPuzzle | null;
}>();

const open = defineModel<boolean>("open", { default: false });
</script>

<template>
  <Dialog v-model:open="open">
    <DialogContent class="max-w-2xl max-h-[90vh] overflow-y-auto">
      <DialogHeader>
        <DialogTitle>Puzzle #{{ puzzle?.puzzle_index ?? 0 }}</DialogTitle>
        <DialogDescription class="sr-only">Details of the selected puzzle</DialogDescription>
      </DialogHeader>

      <div v-if="puzzle" class="space-y-4">
        <!-- Status -->
        <div class="flex items-center gap-2">
          <span class="text-muted-foreground">Result:</span>
          <Badge :variant="get_result_variant(puzzle.result)">
            {{ puzzle.result || puzzle.status }}
          </Badge>
          <span v-if="puzzle.solution_count" class="text-sm text-muted-foreground">
            ({{ puzzle.solution_count }} solution{{ puzzle.solution_count > 1 ? "s" : "" }})
          </span>
        </div>

        <!-- Error message -->
        <div
          v-if="puzzle.error_message"
          class="bg-red-50 dark:bg-red-900/20 p-3 rounded-md text-red-700 dark:text-red-300 text-sm"
        >
          {{ puzzle.error_message }}
        </div>

        <!-- Puzzle Preview -->
        <div class="flex justify-center py-4">
          <PuzzleRenderer :definition="convert_to_definition(puzzle.puzzle_data)" />
        </div>

        <!-- IDs -->
        <div class="space-y-1 text-xs text-muted-foreground">
          <div><span class="font-medium">Definition ID:</span> {{ puzzle.definition_id }}</div>
          <div><span class="font-medium">Solution ID:</span> {{ puzzle.solution_id }}</div>
          <div><span class="font-medium">Complete ID:</span> {{ puzzle.complete_id }}</div>
        </div>

        <!-- Multiple Solutions -->
        <div v-if="puzzle.solutions && puzzle.solutions.length > 1">
          <div class="text-sm font-medium mb-2">Alternative Solutions:</div>
          <div class="grid grid-cols-2 gap-4">
            <div
              v-for="(solution, idx) in puzzle.solutions"
              :key="idx"
              class="border rounded p-2 flex flex-col items-center"
            >
              <div class="text-xs text-muted-foreground mb-1 max-h-fit">Solution {{ idx }}</div>
              <PuzzleRenderer
                class="max-h-fit"
                :show_solution="true"
                :definition="{
                  ...convert_to_definition(puzzle.puzzle_data),
                  solution: solution,
                }"
              />
            </div>
          </div>
          <div v-if="puzzle.solutions.length > 4" class="text-xs text-muted-foreground mt-2">
            + {{ puzzle.solutions.length - 4 }} more solutions
          </div>
        </div>

        <!-- Raw Data -->
        <details class="text-sm">
          <summary class="cursor-pointer text-muted-foreground hover:text-foreground">Raw puzzle data</summary>
          <pre class="bg-muted/50 p-3 rounded-md text-xs overflow-x-auto mt-2">{{
            JSON.stringify(puzzle.puzzle_data, null, 2)
          }}</pre>
        </details>
      </div>
    </DialogContent>
  </Dialog>
</template>
