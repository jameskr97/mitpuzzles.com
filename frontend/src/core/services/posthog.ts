import type { App } from "vue";
import posthog from "posthog-js";
import { useAppStore } from "@/core/store/useAppStore.ts";

export function init_posthog(app: App) {
  const posthog_api_key = import.meta.env.VITE_POSTHOG_API_KEY;

  if (!posthog_api_key) {
    if (import.meta.env.DEV) {
      console.warn("PostHog API key (VITE_POSTHOG_API_KEY) is not set. PostHog will not be initialized.");
    }
    return;
  }

  posthog.init(posthog_api_key, {
    disable_session_recording: window.location.hostname !== "mitpuzzles.com",
    autocapture: true,
    capture_exceptions: true,
  });

  const app_store = useAppStore();
  if (app_store.device_id) {
    posthog.register({ device_id: app_store.device_id });
  }

  app.provide("posthog", posthog);
}

/** capture a structured event to posthog */
export function capture_event(event: string, properties?: Record<string, any>) {
  posthog.capture(event, properties);
}

/** capture error and send to posthog. safe to call with and w/o posthog loaded */
export function capture_error(event: string, error: unknown, properties?: Record<string, any>) {
  console.error(`[${event}]`, error);
  if (!posthog.__loaded) return;
  posthog.capture(event, {
    error_message: error instanceof Error ? error.message : String(error),
    error_stack: error instanceof Error ? error.stack : undefined,
    ...properties,
  });
}

export function posthog_error_handler(err: unknown, instance: any, info: string) {
  console.error(`[Vue Error] ${info}:`, err);
  if (!posthog.__loaded) return;
  posthog.capture("$exception", {
    $exception_message: err instanceof Error ? err.message : String(err),
    $exception_stack: err instanceof Error ? err.stack : undefined,
    $exception_source: "vue_error_handler",
    vue_info: info,
    component: instance?.$options?.name || instance?.$options?.__name || "unknown",
  });
}
