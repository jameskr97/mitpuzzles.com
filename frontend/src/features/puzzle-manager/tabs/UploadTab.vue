<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from "vue";
import { Upload, FileJson, AlertCircle, X, Plus, CheckCircle2, Loader2, Download } from "lucide-vue-next";

import { Badge } from "@/core/components/ui/badge";
import { Button } from "@/core/components/ui/button";
import { ACTIVE_GAMES } from "@/constants";
import Container from "@/core/components/ui/Container.vue";
import { Separator } from "@/core/components/ui/separator";
import {
  Empty,
  EmptyContent,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from "@/core/components/ui/empty";
import { get_status_variant } from "../utils";
import { use_analysis_jobs_store } from "../stores/use_analysis_jobs_store";
import FileDropZone from "../components/FileDropZone.vue";

interface FileEntry {
  file: File;
  id: string;
  puzzle_type: string;
  puzzle_size: string;
  puzzle_difficulty: string;
  game_name: string;
  game_icon: string;
  is_known_type: boolean;
  uploading: boolean;
  upload_error: string | null;
}

interface ActiveJob {
  job_id: string;
  filename: string;
}

const store = use_analysis_jobs_store();
const files = ref<FileEntry[]>([]);
const active_job_ids = ref<string[]>([]);
const drop_zone_ref = ref<InstanceType<typeof FileDropZone> | null>(null);
const rejected_message = ref<string | null>(null);
let rejected_timeout: ReturnType<typeof setTimeout> | null = null;

const parse_file = (file: File): FileEntry | null => {
  const filename = file.name;

  if (!filename.endsWith(".json")) {
    return null;
  }

  const stem = filename.replace(".json", "");
  const parts = stem.split("_");

  if (parts.length < 3) {
    return null;
  }

  const puzzle_type = parts[0].toLowerCase();
  const puzzle_size = parts[1].toLowerCase();
  const puzzle_difficulty = parts[2].toLowerCase();

  const game_info = ACTIVE_GAMES[puzzle_type];
  const is_known_type = !!game_info;

  return {
    file,
    id: `${file.name}-${Date.now()}-${Math.random()}`,
    puzzle_type,
    puzzle_size,
    puzzle_difficulty,
    game_name: game_info?.name || puzzle_type,
    game_icon: game_info?.icon || "?",
    is_known_type,
    uploading: false,
    upload_error: null,
  };
};

const show_rejected_message = (filenames: string[]) => {
  if (rejected_timeout) {
    clearTimeout(rejected_timeout);
  }
  rejected_message.value = `Rejected: ${filenames.join(", ")} (expected {type}_{size}_{difficulty}.json)`;
  rejected_timeout = setTimeout(() => {
    rejected_message.value = null;
  }, 3000);
};

const handle_files_added = (new_files: File[]) => {
  const rejected: string[] = [];
  for (const file of new_files) {
    if (!files.value.some((f) => f.file.name === file.name)) {
      const entry = parse_file(file);
      if (entry) {
        files.value.push(entry);
      } else {
        rejected.push(file.name);
      }
    }
  }
  if (rejected.length > 0) {
    show_rejected_message(rejected);
  }
};

const remove_file = (id: string) => {
  files.value = files.value.filter((f) => f.id !== id);
};

const can_upload = computed(() => files.value.length > 0 && !files.value.some((f) => f.uploading));

const active_jobs = computed(() =>
  active_job_ids.value.map((job_id) => ({
    job_id,
    filename: store.jobs[job_id]?.source_filename || "Unknown",
    job: store.jobs[job_id] || null,
  }))
);

const remove_job = async (job_id: string) => {
  try {
    await store.delete_job(job_id);
  } catch (err) {
    console.error("Error deleting job:", err);
  }
  active_job_ids.value = active_job_ids.value.filter((id) => id !== job_id);
};

const import_unique = async (job_id: string) => {
  try {
    const imported = await store.import_unique(job_id);
    alert(`Imported ${imported} unique puzzles to database`);
    await remove_job(job_id);
  } catch (err: any) {
    console.error("Error importing puzzles:", err);
    alert(err.response?.data?.detail || "Failed to import puzzles");
  }
};

const upload_all = async () => {
  for (const entry of files.value) {
    if (entry.uploading || entry.upload_error) continue;

    entry.uploading = true;
    entry.upload_error = null;

    try {
      const job_id = await store.upload_file(entry.file);
      active_job_ids.value.push(job_id);
      files.value = files.value.filter((f) => f.id !== entry.id);
      store.add_to_polling(job_id);
    } catch (err: any) {
      console.error("Error uploading file:", err);
      entry.upload_error = err.response?.data?.detail || "Upload failed";
      entry.uploading = false;
    }
  }
};

const load_recent_jobs = async () => {
  try {
    const all_jobs = await store.fetch_all_jobs();

    for (const job of all_jobs) {
      if (job.job_type === "file_upload") {
        const created = new Date(job.created_at);
        const one_hour_ago = new Date(Date.now() - 60 * 60 * 1000);
        const is_recent = created > one_hour_ago;
        const is_running = job.status === "pending" || job.status === "running";

        if (is_recent || is_running) {
          active_job_ids.value.push(job.id);
          if (is_running) {
            store.add_to_polling(job.id);
          }
        }
      }
    }
  } catch (err) {
    console.error("Error loading recent jobs:", err);
  }
};

onMounted(() => {
  load_recent_jobs();
});

onUnmounted(() => {
  store.stop_polling();
});
</script>

<template>
  <div class="grid grid-cols-1 md:grid-cols-2 gap-4 items-start">
    <Container class="flex flex-col gap-2">
      <div class="text-2xl font-bold text-center">File Upload</div>
      <Separator class="w-full" />

      <FileDropZone
        ref="drop_zone_ref"
        :accept="['.json']"
        :class="files.length === 0 ? 'flex items-center justify-center' : 'flex flex-col'"
        @files-added="handle_files_added"
      >
        <template #default="{ open_file_picker }">
          <Empty v-if="files.length === 0" class="border-0">
            <EmptyHeader>
              <EmptyMedia variant="icon">
                <FileJson />
              </EmptyMedia>
              <EmptyTitle>Drop puzzle files here</EmptyTitle>
              <EmptyDescription>
                Files should be named: {type}_{size}_{difficulty}.json
              </EmptyDescription>
            </EmptyHeader>
            <EmptyContent>
              <Button @click="open_file_picker">
                <Plus class="h-4 w-4 mr-2" />
                Browse Files
              </Button>
            </EmptyContent>
          </Empty>

          <div v-else class="flex flex-col h-full">
            <div class="flex-1 overflow-auto p-3">
              <div class="grid grid-cols-[auto_1fr_auto_auto_auto] gap-x-3 gap-y-2 items-center">
                <Container v-for="entry in files" :key="entry.id" class="col-span-full grid grid-cols-subgrid">
                  <FileJson class="h-5 w-5 text-muted-foreground" />
                  <div class="font-medium text-sm truncate">{{ entry.file.name }}</div>
                  <div class="text-xs text-muted-foreground whitespace-nowrap">
                    {{ (entry.file.size / 1024).toFixed(1) }} KB
                  </div>
                  <div v-if="entry.upload_error" class="flex items-center gap-1 text-red-500 text-xs">
                    <AlertCircle class="h-3 w-3" />
                    {{ entry.upload_error }}
                  </div>
                  <div v-else class="flex gap-0.5">
                    <Badge :variant="entry.is_known_type ? 'default' : 'secondary'" class="text-xs">
                      {{ entry.game_icon }} {{ entry.game_name }}
                    </Badge>
                    <Badge variant="outline" class="text-xs">{{ entry.puzzle_size }}</Badge>
                    <Badge variant="outline" class="text-xs">{{ entry.puzzle_difficulty }}</Badge>
                  </div>
                  <div class="justify-self-end">
                    <div v-if="entry.uploading" class="text-xs text-muted-foreground">Uploading...</div>
                    <Button v-else variant="ghost" size="icon" class="h-6 w-6" @click="remove_file(entry.id)">
                      <X class="h-4 w-4" />
                    </Button>
                  </div>
                </Container>
              </div>
            </div>
          </div>
        </template>

        <template #footer="{ open_file_picker }">
          <div
            v-if="files.length > 0"
            class="p-3 border-t border-dashed text-center cursor-pointer hover:bg-muted/50 transition-colors"
            @click="open_file_picker"
          >
            <span class="text-sm text-muted-foreground">
              <Plus class="h-4 w-4 inline mr-1" />
              Drop more files or click to browse
            </span>
          </div>
        </template>
      </FileDropZone>

      <div
        v-if="rejected_message"
        class="flex items-center gap-2 p-2 text-sm text-red-500 bg-red-50 dark:bg-red-950 rounded-md"
      >
        <AlertCircle class="h-4 w-4 flex-shrink-0" />
        {{ rejected_message }}
      </div>

      <Button v-if="files.length > 0" @click="upload_all" :disabled="!can_upload" class="w-full">
        <Upload class="h-4 w-4 mr-2" />
        Start Analysis ({{ files.length }} file{{ files.length !== 1 ? "s" : "" }})
      </Button>
    </Container>

    <Container class="flex flex-col gap-2">
      <div class="text-2xl font-bold text-center">Analysis Progress</div>
      <Separator class="w-full" />

      <Empty v-if="active_jobs.length === 0" class="border-0">
        <EmptyHeader>
          <EmptyMedia variant="icon">
            <CheckCircle2 />
          </EmptyMedia>
          <EmptyTitle>No active jobs</EmptyTitle>
          <EmptyDescription>
            Upload files and click "Start Analysis" to begin
          </EmptyDescription>
        </EmptyHeader>
      </Empty>

      <div v-else class="space-y-3 p-2">
        <div
          v-for="active in active_jobs"
          :key="active.job_id"
          class="p-3 rounded-lg border bg-background"
        >
          <div class="flex items-center justify-between mb-2">
            <div class="font-medium text-sm truncate flex-1">{{ active.filename }}</div>
            <Button variant="ghost" size="icon" class="h-6 w-6 flex-shrink-0" @click="remove_job(active.job_id)">
              <X class="h-4 w-4" />
            </Button>
          </div>

          <div v-if="!active.job" class="flex items-center gap-2 text-muted-foreground text-sm">
            <Loader2 class="h-4 w-4 animate-spin" />
            Loading...
          </div>

          <template v-else>
            <div class="flex items-center gap-2 mb-2">
              <Badge :variant="get_status_variant(active.job.status)">
                {{ active.job.status }}
              </Badge>
              <span class="text-xs text-muted-foreground">
                {{ active.job.processed_count }}/{{ active.job.total_puzzles }} puzzles
              </span>
              <Loader2 v-if="active.job.status === 'running'" class="h-3 w-3 animate-spin text-muted-foreground" />
              <CheckCircle2 v-else-if="active.job.status === 'completed'" class="h-3 w-3 text-green-500" />
            </div>

            <div class="h-1.5 bg-muted rounded-full overflow-hidden mb-2">
              <div
                class="h-full bg-primary transition-all duration-300"
                :style="{ width: `${(active.job.processed_count / active.job.total_puzzles) * 100}%` }"
              />
            </div>

            <div v-if="active.job.processed_count > 0" class="flex gap-1 flex-wrap">
              <Badge v-if="active.job.unique_count > 0" variant="green" class="text-xs">
                {{ active.job.unique_count }} unique
              </Badge>
              <Badge v-if="active.job.invalid_count > 0" variant="red" class="text-xs">
                {{ active.job.invalid_count }} invalid
              </Badge>
              <Badge v-if="active.job.multi_solution_count > 0" variant="secondary" class="text-xs">
                {{ active.job.multi_solution_count }} multi
              </Badge>
              <Badge v-if="active.job.duplicate_count > 0" variant="secondary" class="text-xs">
                {{ active.job.duplicate_count }} dupe
              </Badge>
              <Badge v-if="active.job.error_count > 0" variant="red" class="text-xs">
                {{ active.job.error_count }} errors
              </Badge>
            </div>

            <Button
              v-if="active.job.status === 'completed' && active.job.unique_count > 0"
              size="sm"
              class="mt-2 w-full"
              @click="import_unique(active.job_id)"
            >
              <Download class="h-4 w-4 mr-2" />
              Import {{ active.job.unique_count }} Unique Puzzles
            </Button>
          </template>
        </div>
      </div>
    </Container>
  </div>
</template>
