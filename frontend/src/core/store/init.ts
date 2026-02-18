import { useAppStore } from "@/core/store/useAppStore.ts";
import { useAuthStore } from "@/core/store/useAuthStore.ts";
import { useSessionTrackingStore } from "@/core/store/useSessionTrackingStore.ts";
import { usePuzzleMetadataStore } from "@/core/store/puzzle/usePuzzleMetadataStore.ts";
import { usePuzzleProgressStore } from "@/core/store/puzzle/usePuzzleProgressStore.ts";
import { usePuzzleHistoryStore } from "@/core/store/puzzle/usePuzzleHistoryStore.ts";
import { usePuzzleScaleStore } from "@/core/store/puzzle/usePuzzleScaleStore.ts";

export async function init_app_store() {
  const app_store = useAppStore();
  app_store.init_consent();
  await app_store.updateDeviceFingerprint();
  app_store.initCacheVersion();
}

export async function init_session_tracking() {
  const session_tracker = useSessionTrackingStore();
  await session_tracker.initialize();
}

export async function init_auth() {
  const auth_store = useAuthStore();
  await auth_store.initializeAuth();
}

export async function init_puzzle_stores() {
  await Promise.all([
    usePuzzleScaleStore().init(),
    usePuzzleProgressStore().init(),
    usePuzzleMetadataStore().initializeStore(),
    usePuzzleHistoryStore().init(),
  ]);
}
