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

import { OhVueIcon } from "@/icons";
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
import { useSessionTrackingStore } from "@/store/useSessionTrackingStore.ts";
import { registerSW } from "virtual:pwa-register";
import { I18NextVue, i18next } from "@/i18n.ts";

if (import.meta.hot) {
  import.meta.hot.accept(["./constants.ts"], () => {
    import.meta.hot!.invalidate();
  });
}

StorageVersionManager.clearOldStorage(); // clear old storage if needed

// Register service worker for PWA
const update_sw = registerSW({
  onNeedRefresh() {
    logger.debug("Service worker needs refresh");
  },
  onOfflineReady() {
    logger.debug("App ready to work offline");
  },
});

const route = {
  view: (path: string, name: string, view: string, sidebar: boolean = true, requireLoggedIn: boolean = false) => ({
    path,
    name,
    component: () => import(`@/views/${view}.vue`),
    meta: { showSidebar: sidebar, requireLoggedIn },
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
    component: ACTIVE_GAMES[name].freeplay,
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
    route.view("/reset-password", "reset-password", "ResetPassword", false),
    route.view("/account", "account", "AccountSettings", true, true),
    route.view("/about-us", "about-us", "AboutUs"),
    route.view("/privacy-policy", "privacy-policy", "privacy-policy"),
    route.view("/board2", "board2", "board2"),
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
      })
      .use(I18NextVue,  { i18next });
      maintenanceApp.mount("#app");
      return;
    }
  } catch (error) {
    // 404 or network error - maintenance mode is OFF, continue with normal startup
  }
  logger.debug("Bootstrapping app...");
  const router = createRouter(routerConfig);
  const app = createApp(App)
    .use(createPinia())
    .use(router)
    .use(I18NextVue,  { i18next })
    .component("v-icon", OhVueIcon);

  // get local device id
  // every user has a device fingerprint. this is used for anonymous tracking and analytics.
  // when the user is logged-in, they're associated by both user ID and device fingerprint.
  const appStore = useAppStore();
  await appStore.updateDeviceFingerprint();
  appStore.initCacheVersion();

  // initialize session tracking after device fingerprint is available
  const sessionTracker = useSessionTrackingStore();
  await sessionTracker.initialize();

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
  if (currentRoute.meta.requireLoggedIn && !authStore.isAuthenticated) {
    console.log('Initial route requires login, redirecting to Home');
    await router.replace({ name: "Home" });
  }

  // set up router guard after auth initialization
  router.beforeEach(async (to, from, next) => {
    console.log(`Navigating to ${to.fullPath} from ${from.fullPath}`);
    const isAdmin = authStore.isAdmin;
    const isAuthenticated = authStore.isAuthenticated;
    const requiresAdmin = to.meta.requiresAdmin || false;
    const requireLoggedIn = to.meta.requireLoggedIn || false;

    if (requiresAdmin && !isAdmin) {
      console.log('Access denied: Admins only');
      next({ name: "Home" });
    } else if (requireLoggedIn && !isAuthenticated) {
      console.log('Access denied: Login required');
      next({ name: "Home" });
    } else {
      next();
    }
  });

  // initialize indexeddb + pinia stores
  await Promise.all([
    usePuzzleScaleStore().init(),
    usePuzzleProgressStore().init(),
    usePuzzleMetadataStore().initializeStore(),
    usePuzzleHistoryStore().init(),
  ]);
  app.mount("#app");
})();
