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
  });

  const app_store = useAppStore();
  if (app_store.device_id) {
    posthog.register({ device_id: app_store.device_id });
  }

  app.provide("posthog", posthog);
}
