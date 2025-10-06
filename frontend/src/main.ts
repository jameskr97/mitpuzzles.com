// Vue core
import { createApp, h } from "vue";
import { createRouter, createWebHistory, type RouterOptions } from "vue-router";
// Pinia store
import { createPinia } from "pinia";
import { useAuthStore } from "@/store/useAuthStore.ts";
import { useAppStore } from "@/store/useAppStore.ts";
// Components & Views
import App from "./App.vue";
import MarkdownPage from "@/views/MarkdownPage.vue";
import ExperimentRunner from "@/features/experiment-core/components/ExperimentRunner.vue";
import Freeplay from "@/components/Freeplay.vue";
import { OhVueIcon } from "@/icons";
// Markdown content
import mdAbout from "./views/aboutus.md?raw";
// Utility
import { StorageVersionManager } from "@/utils.ts";
// Style
import "./style.css";
// PostHog
import posthog from "posthog-js";
// Socket
import { ACTIVE_GAMES, ADMIN_TOOLS, DEV_TOOLS } from "@/constants.ts";
import logger from "@/services/logger.ts";
import { usePuzzleMetadataStore } from "@/store/puzzle/usePuzzleMetadataStore.ts";
import { usePuzzleProgressStore } from "@/store/puzzle/usePuzzleProgressStore.ts";
import { usePuzzleHistoryStore } from "@/store/puzzle/usePuzzleHistoryStore.ts";
import { usePuzzleScaleStore } from "@/store/puzzle/usePuzzleScaleStore.ts";
import { init_cached_endpoints } from "@/store/database/HTTPCache.ts";

if (import.meta.hot) {
  import.meta.hot.accept(["./constants.ts"], () => {
    import.meta.hot!.invalidate();
  });
}

StorageVersionManager.clearOldStorage(); // clear old storage if needed

const route = {
  view: (path: string, name: string, view: string, sidebar: boolean = true) => ({
    path,
    name,
    component: () => import(`@/views/${view}.vue`),
    meta: { showSidebar: sidebar },
  }),
  admin: (path: string, name: string, view: string, sidebar: boolean = true) => ({
    path,
    name,
    component: () => import(`@/views/${view}.vue`),
    meta: { showSidebar: sidebar, requiresAdmin: true },
  }),
  markdown: (path: string, name: string, content: string, proseClass = "prose-lg") => ({
    path,
    name,
    component: {
      render: () => h(MarkdownPage, { content, proseClass }),
    },
  }),
  game: (name: string) => ({
    path: `/${name}`,
    name: `game-${name}`,
    component: Freeplay,
    meta: { game_type: name },
  }),
  dev: (key: string, meta: Object) => ({
    path: `/devtool/${key}`,
    name: `dev-${key}`,
    component: () => import(`@/views/dev/${key}.vue`),
    meta: { ...meta, requiresAdmin: true },
  }),
};

/** This is the global list of routes that are available in the app. */
const routerConfig: RouterOptions = {
  history: createWebHistory(),
  routes: [
    route.view("", "Home", "Home"),
    ...Object.values(ADMIN_TOOLS).map((tool) => route.admin(tool.route_path, tool.key, tool.key)),
    route.view("/signup", "signup", "Signup", false),
    route.view("/verify-email", "verify-email", "SignupVerifyEmail", false),
    route.markdown("/about-us", "about-us", mdAbout),
    ...Object.values(DEV_TOOLS).map(({ key, meta }) => route.dev(key, meta)),
    ...Object.keys(ACTIVE_GAMES).map(route.game),
    {
      path: "/experiment/:experiment_id",
      name: "experiment",
      component: ExperimentRunner,
      meta: {
        showSidebar: () => {
          return !new URLSearchParams(window.location.search).has("PROLIFIC_PID");
        },
      },
    },
    { path: "/:pathMatch(.*)*", name: "404", component: () => import("./views/404.vue") },
  ],
};

/** app initialization */
(async () => {
  // check for maintenance mode before initializing full app
  try {
    const response = await fetch("/maintenance.json");
    if (response.ok) {
      const maintenanceData = await response.json();
      // if file exists, we're in maintenance mode
      const { default: MaintenanceMode } = await import("@/components/MaintenanceMode.vue");
      const maintenanceApp = createApp(MaintenanceMode, {
        reason: maintenanceData.reason || null,
      });
      maintenanceApp.mount("#app");
      return;
    }
  } catch (error) {
    // 404 or network error - maintenance mode is OFF, continue with normal startup
  }
  logger.debug("Bootstrapping app...");
  const router = createRouter(routerConfig);
  const app = createApp(App).use(createPinia()).use(router).component("v-icon", OhVueIcon);

  // get local device id
  // every user has a device fingerprint. this is used for anonymous tracking and analytics.
  // when the user is logged-in, they're associated by both user ID and device fingerprint.
  const appStore = useAppStore();
  await appStore.updateDeviceFingerprint();
  appStore.initCacheVersion();

  // posthog
  const posthogApiKey = import.meta.env.VITE_POSTHOG_API_KEY;
  if (posthogApiKey) {
    posthog.init(posthogApiKey, {
      disable_session_recording: window.location.hostname !== "mitpuzzles.com", // only enable session recording on production
    });

    // register device_id with all posthog events
    const appStore = useAppStore();
    if (appStore.device_id) posthog.register({ device_id: appStore.device_id });
    app.provide("posthog", posthog);
  } else {
    if (import.meta.env.DEV) {
      console.warn("PostHog API key (VITE_POSTHOG_API_KEY) is not set. PostHog will not be initialized.");
    }
  }

  // initialize auth first
  const authStore = useAuthStore();
  await authStore.initializeAuth();

  // check initial route after auth is initialized but BEFORE mounting
  const currentRoute = router.currentRoute.value;
  if (currentRoute.meta.requiresAdmin && !authStore.isAdmin) {
    console.log('Initial route requires admin, redirecting to Home');
    await router.replace({ name: "Home" });
  }

  // set up router guard after auth initialization
  router.beforeEach(async (to, from, next) => {
    console.log(`Navigating to ${to.fullPath} from ${from.fullPath}`);
    const isAdmin = authStore.isAdmin;
    const requiresAdmin = to.meta.requiresAdmin || false;

    if (requiresAdmin && !isAdmin) {
      console.log('Access denied: Admins only');
      next({ name: "Home" });
    } else {
      next();
    }
  });

  init_cached_endpoints();

  // initialize indexeddb + pinia stores
  await Promise.all([
    usePuzzleScaleStore().init(),
    usePuzzleProgressStore().init(),
    usePuzzleMetadataStore().initializeStore(),
    usePuzzleHistoryStore().init(),
  ]);
  app.mount("#app");
})();
