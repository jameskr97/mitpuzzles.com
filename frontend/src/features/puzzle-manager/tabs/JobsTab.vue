<script setup lang="ts">
import type { ColumnDef, SortingState } from "@tanstack/vue-table";
import {
  FlexRender,
  getCoreRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useVueTable,
} from "@tanstack/vue-table";
import { ArrowUpDown, RefreshCw, Trash2, Eye, ChevronLeft } from "lucide-vue-next";
import { h, onMounted, onUnmounted, ref } from "vue";
import { api } from "@/core/services/client";

import { valueUpdater } from "@/core/components/ui/table/utils";
import { Badge } from "@/core/components/ui/badge";
import { Button } from "@/core/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/core/components/ui/table";
import type { BackgroundJob, AnalysisJobPuzzle } from "../types";
import { format_date, get_status_variant } from "../utils";
import JobSummary from "../components/JobSummary.vue";
import PuzzleGrid from "../components/PuzzleGrid.vue";
import PuzzleDetailModal from "../components/PuzzleDetailModal.vue";

// State
const jobs = ref<BackgroundJob[]>([]);
const loading = ref(false);
const error = ref<string | null>(null);

// Job detail view
const selected_job = ref<BackgroundJob | null>(null);

// Puzzle detail modal
const selected_puzzle = ref<AnalysisJobPuzzle | null>(null);
const puzzle_modal_open = ref(false);

// Polling for real-time updates
let poll_interval: ReturnType<typeof setInterval> | null = null;

const get_progress_text = (job: BackgroundJob) => {
  if (job.status === "completed") {
    return `${job.total_puzzles} puzzles`;
  }
  return `${job.processed_count}/${job.total_puzzles}`;
};

// Table columns
const columns: ColumnDef<BackgroundJob>[] = [
  {
    accessorKey: "created_at",
    header: ({ column }) => {
      return h(
        Button,
        {
          variant: "ghost",
          onClick: () => column.toggleSorting(column.getIsSorted() === "asc"),
        },
        () => ["Date", h(ArrowUpDown, { class: "ml-2 h-4 w-4" })],
      );
    },
    cell: ({ row }) => h("div", { class: "whitespace-nowrap" }, format_date(row.getValue("created_at"))),
  },
  {
    accessorKey: "puzzle_type",
    header: "Type",
    cell: ({ row }) => h("div", { class: "font-medium" }, row.getValue("puzzle_type")),
  },
  {
    accessorKey: "source_filename",
    header: "Source",
    cell: ({ row }) => {
      const filename = row.getValue("source_filename") as string | null;
      return h("div", { class: "max-w-[200px] truncate" }, filename || "-");
    },
  },
  {
    accessorKey: "status",
    header: "Status",
    cell: ({ row }) => {
      const status = row.getValue("status") as string;
      return h(Badge, { variant: get_status_variant(status) }, () => status);
    },
  },
  {
    accessorKey: "total_puzzles",
    header: "Progress",
    cell: ({ row }) => h("div", {}, get_progress_text(row.original)),
  },
  {
    id: "results",
    header: "Results",
    cell: ({ row }) => {
      const job = row.original;
      return h(
        "div",
        { class: "flex gap-1 flex-wrap" },
        [
          job.unique_count > 0 && h(Badge, { variant: "green", class: "text-xs" }, () => `${job.unique_count} unique`),
          job.invalid_count > 0 && h(Badge, { variant: "red", class: "text-xs" }, () => `${job.invalid_count} invalid`),
          job.multi_solution_count > 0 &&
            h(Badge, { variant: "secondary", class: "text-xs" }, () => `${job.multi_solution_count} multi`),
          job.duplicate_count > 0 &&
            h(Badge, { variant: "secondary", class: "text-xs" }, () => `${job.duplicate_count} dupe`),
          job.error_count > 0 && h(Badge, { variant: "red", class: "text-xs" }, () => `${job.error_count} errors`),
        ].filter(Boolean),
      );
    },
  },
];

const sorting = ref<SortingState>([{ id: "created_at", desc: true }]);

const table = useVueTable({
  get data() {
    return jobs.value;
  },
  columns,
  getCoreRowModel: getCoreRowModel(),
  getPaginationRowModel: getPaginationRowModel(),
  getSortedRowModel: getSortedRowModel(),
  onSortingChange: (updaterOrValue) => valueUpdater(updaterOrValue, sorting),
  state: {
    get sorting() {
      return sorting.value;
    },
  },
});

// Polling for job updates
const has_running_jobs = () => {
  return jobs.value.some((j) => j.status === "running" || j.status === "pending");
};

const poll_running_jobs = async () => {
  if (!has_running_jobs()) {
    stop_polling();
    return;
  }

  try {
    const { data } = await api.GET("/api/analysis/jobs");
    jobs.value = (data ?? []) as any;

    // Update selected job if it's in the list
    if (selected_job.value) {
      const updated = jobs.value.find((j) => j.id === selected_job.value?.id);
      if (updated) {
        selected_job.value = updated;
      }
    }
  } catch (err) {
    console.error("Error polling jobs:", err);
  }
};

const start_polling = () => {
  if (poll_interval) return;
  poll_interval = setInterval(poll_running_jobs, 5000);
};

const stop_polling = () => {
  if (poll_interval) {
    clearInterval(poll_interval);
    poll_interval = null;
  }
};

const check_and_start_polling = () => {
  if (has_running_jobs()) {
    start_polling();
  }
};

// API calls
const fetch_jobs = async () => {
  try {
    loading.value = true;
    error.value = null;
    const { data } = await api.GET("/api/analysis/jobs");
    jobs.value = (data ?? []) as any;

    // Start polling if there are running jobs
    check_and_start_polling();
  } catch (err) {
    error.value = "Failed to load analysis jobs";
    console.error("Error fetching jobs:", err);
  } finally {
    loading.value = false;
  }
};

const restart_job = async (job_id: string) => {
  try {
    await api.POST("/api/analysis/jobs/{job_id}/restart", { params: { path: { job_id } } });
    await fetch_jobs();
  } catch (err) {
    console.error("Error restarting job:", err);
  }
};

const delete_job = async (job_id: string) => {
  if (!confirm("Are you sure you want to delete this job?")) return;

  try {
    await api.DELETE("/api/analysis/jobs/{job_id}", { params: { path: { job_id } } });
    if (selected_job.value?.id === job_id) {
      selected_job.value = null;
    }
    await fetch_jobs();
  } catch (err) {
    console.error("Error deleting job:", err);
  }
};

const view_job = (job: BackgroundJob) => {
  selected_job.value = job;
};

const open_puzzle_detail = (puzzle: AnalysisJobPuzzle) => {
  selected_puzzle.value = puzzle;
  puzzle_modal_open.value = true;
};

const handle_refresh = async () => {
  await fetch_jobs();
  if (selected_job.value) {
    const updated = jobs.value.find((j) => j.id === selected_job.value?.id);
    if (updated) {
      selected_job.value = updated;
    }
  }
};

onMounted(() => {
  fetch_jobs();
});

onUnmounted(() => {
  stop_polling();
});
</script>

<template>
  <div class="w-full">
    <!-- Back button when viewing job detail -->
    <div v-if="selected_job" class="mb-4">
      <Button variant="ghost" size="sm" @click="selected_job = null">
        <ChevronLeft class="h-4 w-4 mr-1" />
        Back to Jobs
      </Button>
    </div>

    <!-- Job List View -->
    <div v-if="!selected_job">
      <div class="flex items-center justify-between mb-4">
        <div class="text-lg font-medium">Analysis Jobs</div>
        <Button variant="outline" size="sm" @click="fetch_jobs" :disabled="loading">
          <RefreshCw :class="['h-4 w-4 mr-2', loading && 'animate-spin']" />
          Refresh
        </Button>
      </div>

      <div v-if="loading" class="text-muted-foreground text-center py-8">Loading...</div>
      <div v-else-if="error" class="text-red-500 text-center py-8">{{ error }}</div>
      <template v-else>
        <div class="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow v-for="headerGroup in table.getHeaderGroups()" :key="headerGroup.id">
                <TableHead v-for="header in headerGroup.headers" :key="header.id">
                  <FlexRender
                    v-if="!header.isPlaceholder"
                    :render="header.column.columnDef.header"
                    :props="header.getContext()"
                  />
                </TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <template v-if="table.getRowModel().rows?.length">
                <TableRow
                  v-for="row in table.getRowModel().rows"
                  :key="row.id"
                  class="cursor-pointer hover:bg-muted/50"
                  @click="view_job(row.original)"
                >
                  <TableCell v-for="cell in row.getVisibleCells()" :key="cell.id">
                    <FlexRender :render="cell.column.columnDef.cell" :props="cell.getContext()" />
                  </TableCell>
                  <TableCell @click.stop>
                    <div class="flex gap-1">
                      <Button variant="ghost" size="sm" @click="view_job(row.original)" title="View puzzles">
                        <Eye class="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        @click="restart_job(row.original.id)"
                        :disabled="row.original.status === 'running'"
                        title="Restart job"
                      >
                        <RefreshCw class="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="sm" @click="delete_job(row.original.id)" title="Delete job">
                        <Trash2 class="h-4 w-4 text-red-500" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              </template>
              <TableRow v-else>
                <TableCell :colspan="columns.length + 1" class="h-24 text-center">
                  No analysis jobs yet. Use the CLI or Database Audit tab to analyze puzzles.
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </div>
        <div class="flex items-center justify-end space-x-2 py-4">
          <div class="flex-1 text-sm text-muted-foreground">{{ jobs.length }} job(s)</div>
          <div class="space-x-2">
            <Button variant="outline" size="sm" :disabled="!table.getCanPreviousPage()" @click="table.previousPage()">
              Previous
            </Button>
            <Button variant="outline" size="sm" :disabled="!table.getCanNextPage()" @click="table.nextPage()">
              Next
            </Button>
          </div>
        </div>
      </template>
    </div>

    <!-- Job Detail View -->
    <div v-else>
      <JobSummary :job="selected_job" @refresh="handle_refresh" class="mb-4" />
      <PuzzleGrid :job="selected_job" @select-puzzle="open_puzzle_detail" />
    </div>

    <!-- Puzzle Detail Modal -->
    <PuzzleDetailModal v-model:open="puzzle_modal_open" :puzzle="selected_puzzle" />
  </div>
</template>
