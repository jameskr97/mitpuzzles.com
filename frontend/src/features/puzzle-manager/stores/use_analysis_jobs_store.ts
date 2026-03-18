import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { api } from "@/core/services/client";
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
    const { data } = await api.GET("/api/analysis/jobs/{job_id}", { params: { path: { job_id } } });
    const job = data as unknown as BackgroundJob;
    jobs.value[job_id] = job;
    return job;
  }

  async function fetch_all_jobs(): Promise<BackgroundJob[]> {
    const { data } = await api.GET("/api/analysis/jobs");
    const all = (data ?? []) as unknown as BackgroundJob[];
    for (const job of all) {
      jobs.value[job.id] = job;
    }
    return all;
  }

  async function upload_file(file: File): Promise<string | null> {
    const form_data = new FormData();
    form_data.append("file", file);

    const { data, error } = await api.POST("/api/analysis/upload", {
      body: form_data as any,
      bodySerializer: (b: any) => b,
    });
    if (error) return null;
    return (data as any)?.job_id;
  }

  async function start_database_audit(puzzle_type: string): Promise<string | null> {
    const { data, error } = await api.POST("/api/analysis/analyze-database", {
      body: { puzzle_type } as any,
    });
    if (error) return null;
    return (data as any)?.job_id;
  }

  async function import_unique(job_id: string): Promise<number | null> {
    const { data, error } = await api.POST("/api/analysis/jobs/{job_id}/import-unique", { params: { path: { job_id } } });
    if (error) return null;
    return (data as any)?.imported;
  }

  async function disable_non_unique(job_id: string): Promise<number | null> {
    const { data, error } = await api.POST("/api/analysis/jobs/{job_id}/disable-non-unique", { params: { path: { job_id } } });
    if (error) return null;
    return (data as any)?.disabled;
  }

  async function delete_job(job_id: string): Promise<void> {
    await api.DELETE("/api/analysis/jobs/{job_id}", { params: { path: { job_id } } });
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
