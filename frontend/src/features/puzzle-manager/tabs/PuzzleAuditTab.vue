<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from "vue";
import { Play, Loader2, CheckCircle2, Ban } from "lucide-vue-next";

import { Badge } from "@/core/components/ui/badge";
import { Button } from "@/core/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/core/components/ui/table";
import { ACTIVE_GAMES } from "@/constants";
import { get_status_variant } from "../utils";
import { use_analysis_jobs_store } from "../stores/use_analysis_jobs_store";

interface AuditState {
  job_id: string | null;
  loading: boolean;
}

const store = use_analysis_jobs_store();
const puzzle_types = Object.keys(ACTIVE_GAMES);
const audit_states = ref<Record<string, AuditState>>({});

for (const ptype of puzzle_types) {
  audit_states.value[ptype] = { job_id: null, loading: false };
}

const get_job = (ptype: string) => {
  const job_id = audit_states.value[ptype].job_id;
  return job_id ? store.jobs[job_id] : null;
};

const has_running_jobs = computed(() => {
  return puzzle_types.some((ptype) => {
    const job = get_job(ptype);
    return job?.status === "pending" || job?.status === "running";
  });
});

const run_audit = async (puzzle_type: string) => {
  const state = audit_states.value[puzzle_type];
  state.loading = true;

  try {
    const job_id = await store.start_database_audit(puzzle_type);
    state.job_id = job_id;
    await store.fetch_job(job_id);
    store.add_to_polling(job_id);
  } catch (err: any) {
    console.error("Error starting audit:", err);
    alert(err.response?.data?.detail || "Failed to start audit");
  } finally {
    state.loading = false;
  }
};

const disable_non_unique = async (puzzle_type: string) => {
  const job = get_job(puzzle_type);
  if (!job) return;

  const count = job.multi_solution_count + job.invalid_count;
  if (!confirm(`This will disable ${count} non-unique/invalid puzzles. Continue?`)) {
    return;
  }

  try {
    const disabled = await store.disable_non_unique(job.id);
    alert(`Disabled ${disabled} puzzles`);
    await store.delete_job(job.id);
    audit_states.value[puzzle_type].job_id = null;
  } catch (err: any) {
    console.error("Error disabling puzzles:", err);
    alert(err.response?.data?.detail || "Failed to disable puzzles");
  }
};

const clear_result = async (puzzle_type: string) => {
  const job = get_job(puzzle_type);
  if (!job) return;

  try {
    await store.delete_job(job.id);
    audit_states.value[puzzle_type].job_id = null;
  } catch (err) {
    console.error("Error clearing result:", err);
  }
};

const load_existing_jobs = async () => {
  try {
    const all_jobs = await store.fetch_all_jobs();

    for (const job of all_jobs) {
      if (job.job_type === "database_audit") {
        const ptype = job.puzzle_type;
        if (ptype in audit_states.value) {
          const current_id = audit_states.value[ptype].job_id;
          const current_job = current_id ? store.jobs[current_id] : null;

          if (!current_job || new Date(job.created_at) > new Date(current_job.created_at)) {
            audit_states.value[ptype].job_id = job.id;
          }
        }
      }
    }

    if (has_running_jobs.value) {
      const running_ids = puzzle_types
        .map((ptype) => audit_states.value[ptype].job_id)
        .filter((id): id is string => {
          if (!id) return false;
          const job = store.jobs[id];
          return job?.status === "pending" || job?.status === "running";
        });
      if (running_ids.length > 0) {
        store.start_polling(running_ids);
      }
    }
  } catch (err) {
    console.error("Error loading existing jobs:", err);
  }
};

onMounted(() => {
  load_existing_jobs();
});

onUnmounted(() => {
  store.stop_polling();
});
</script>

<template>
  <div>
    <div class="mb-4">
      <div class="text-lg font-medium">Puzzle Audit</div>
      <p class="text-sm text-muted-foreground">
        Check existing puzzles in the database for uniqueness. Non-unique puzzles can be disabled from distribution.
      </p>
    </div>

    <div class="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Puzzle Type</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Results</TableHead>
            <TableHead class="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow v-for="ptype in puzzle_types" :key="ptype">
            <TableCell class="font-medium">
              {{ ACTIVE_GAMES[ptype].icon }} {{ ACTIVE_GAMES[ptype].name }}
            </TableCell>

            <TableCell>
              <template v-if="audit_states[ptype].loading">
                <div class="flex items-center gap-2 text-muted-foreground text-sm">
                  <Loader2 class="h-4 w-4 animate-spin" />
                  Starting...
                </div>
              </template>
              <template v-else-if="get_job(ptype)">
                <div class="flex items-center gap-2">
                  <Badge :variant="get_status_variant(get_job(ptype)!.status)">
                    {{ get_job(ptype)!.status }}
                  </Badge>
                  <Loader2
                    v-if="get_job(ptype)!.status === 'running'"
                    class="h-3 w-3 animate-spin text-muted-foreground"
                  />
                  <CheckCircle2
                    v-else-if="get_job(ptype)!.status === 'completed'"
                    class="h-3 w-3 text-green-500"
                  />
                  <span class="text-xs text-muted-foreground">
                    {{ get_job(ptype)!.processed_count }}/{{ get_job(ptype)!.total_puzzles }}
                  </span>
                </div>
              </template>
              <span v-else class="text-muted-foreground text-sm">-</span>
            </TableCell>

            <TableCell>
              <div v-if="get_job(ptype)?.status === 'completed'" class="flex gap-1 flex-wrap">
                <Badge variant="green" class="text-xs">
                  {{ get_job(ptype)!.unique_count }} unique
                </Badge>
                <Badge
                  v-if="get_job(ptype)!.multi_solution_count > 0"
                  variant="secondary"
                  class="text-xs"
                >
                  {{ get_job(ptype)!.multi_solution_count }} multi
                </Badge>
                <Badge v-if="get_job(ptype)!.invalid_count > 0" variant="red" class="text-xs">
                  {{ get_job(ptype)!.invalid_count }} invalid
                </Badge>
                <Badge v-if="get_job(ptype)!.disabled_count > 0" variant="outline" class="text-xs">
                  {{ get_job(ptype)!.disabled_count }} disabled
                </Badge>
              </div>
              <span v-else class="text-muted-foreground text-sm">-</span>
            </TableCell>

            <TableCell class="text-right">
              <div class="flex gap-2 justify-end">
                <Button
                  v-if="!get_job(ptype) || get_job(ptype)!.status === 'completed'"
                  variant="outline"
                  size="sm"
                  @click="run_audit(ptype)"
                  :disabled="audit_states[ptype].loading"
                >
                  <Play v-if="!audit_states[ptype].loading" class="h-4 w-4 mr-1" />
                  <Loader2 v-else class="h-4 w-4 mr-1 animate-spin" />
                  {{ audit_states[ptype].loading ? "Starting..." : "Run" }}
                </Button>

                <Button
                  v-if="
                    get_job(ptype)?.status === 'completed' &&
                    (get_job(ptype)!.multi_solution_count > 0 || get_job(ptype)!.invalid_count > 0)
                  "
                  variant="destructive"
                  size="sm"
                  @click="disable_non_unique(ptype)"
                >
                  <Ban class="h-4 w-4 mr-1" />
                  Disable ({{ get_job(ptype)!.multi_solution_count + get_job(ptype)!.invalid_count }})
                </Button>

                <Button
                  v-if="
                    get_job(ptype)?.status === 'completed' &&
                    get_job(ptype)!.multi_solution_count === 0 &&
                    get_job(ptype)!.invalid_count === 0
                  "
                  variant="outline"
                  size="sm"
                  @click="clear_result(ptype)"
                >
                  Clear
                </Button>
              </div>
            </TableCell>
          </TableRow>
        </TableBody>
      </Table>
    </div>
  </div>
</template>
