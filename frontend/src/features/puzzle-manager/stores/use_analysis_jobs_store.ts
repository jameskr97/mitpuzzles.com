import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { api } from "@/core/services/axios";
import type { BackgroundJob } from "../types";

export const use_analysis_jobs_store = defineStore("analysis_jobs", () => {
  const jobs = ref<Record<string, BackgroundJob>>({});
  let poll_interval: ReturnType<typeof setInterval> | null = null;
  let poll_job_ids: Set<string> = new Set();

  const is_polling = computed(() => poll_interval !== null);

  function get_job(job_id: string): BackgroundJob | undefined {
    return jobs.value[job_id];
  }

  async function fetch_job(job_id: string): Promise<BackgroundJob> {
    const response = await api.get(`/api/analysis/jobs/${job_id}`);
    jobs.value[job_id] = response.data;
    return response.data;
  }

  async function fetch_all_jobs(): Promise<BackgroundJob[]> {
    const response = await api.get("/api/analysis/jobs");
    for (const job of response.data) {
      jobs.value[job.id] = job;
    }
    return response.data;
  }

  async function upload_file(file: File): Promise<string> {
    const form_data = new FormData();
    form_data.append("file", file);

    const response = await api.post("/api/analysis/upload", form_data, {
      headers: { "Content-Type": "multipart/form-data" },
    });

    return response.data.job_id;
  }

  async function start_database_audit(puzzle_type: string): Promise<string> {
    const response = await api.post("/api/analysis/analyze-database", {
      puzzle_type,
    });
    return response.data.job_id;
  }

  async function import_unique(job_id: string): Promise<number> {
    const response = await api.post(`/api/analysis/jobs/${job_id}/import-unique`);
    return response.data.imported;
  }

  async function disable_non_unique(job_id: string): Promise<number> {
    const response = await api.post(`/api/analysis/jobs/${job_id}/disable-non-unique`);
    return response.data.disabled;
  }

  async function delete_job(job_id: string): Promise<void> {
    await api.delete(`/api/analysis/jobs/${job_id}`);
    delete jobs.value[job_id];
    poll_job_ids.delete(job_id);
  }

  async function poll_jobs() {
    for (const job_id of poll_job_ids) {
      const job = jobs.value[job_id];
      if (!job || job.status === "pending" || job.status === "running") {
        try {
          await fetch_job(job_id);
        } catch (err) {
          console.error(`Error polling job ${job_id}:`, err);
        }
      }
    }

    const has_active = Array.from(poll_job_ids).some((id) => {
      const job = jobs.value[id];
      return !job || job.status === "pending" || job.status === "running";
    });

    if (!has_active) {
      stop_polling();
    }
  }

  function start_polling(job_ids: string[]) {
    for (const id of job_ids) {
      poll_job_ids.add(id);
    }

    if (poll_interval) return;
    poll_jobs();
    poll_interval = setInterval(poll_jobs, 500);
  }

  function stop_polling() {
    if (poll_interval) {
      clearInterval(poll_interval);
      poll_interval = null;
    }
    poll_job_ids.clear();
  }

  function add_to_polling(job_id: string) {
    poll_job_ids.add(job_id);
    if (!poll_interval) {
      poll_jobs();
      poll_interval = setInterval(poll_jobs, 500);
    }
  }

  return {
    jobs,
    is_polling,
    get_job,
    fetch_job,
    fetch_all_jobs,
    upload_file,
    start_database_audit,
    import_unique,
    disable_non_unique,
    delete_job,
    start_polling,
    stop_polling,
    add_to_polling,
  };
});
