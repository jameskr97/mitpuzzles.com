// Vue core
import { createApp, h } from "vue";
import { createRouter, createWebHistory, type RouterOptions } from "vue-router";
// Pinia store
import { createPinia } from "pinia";
import { useAuthStore } from "@/store/auth.ts";
import { useVisitorStore } from "@/store/visitor.ts";
// Components & Views
import App from "./App.vue";
import MarkdownPage from "@/views/MarkdownPage.vue";
import { OhVueIcon } from "@/icons";
// Markdown content
import mdAbout from "./views/aboutus.md?raw";
// Utility
import { detectModeFromPath, StorageVersionManager } from "@/utils.ts";
// Style
import "./style.css";
// PostHog
import posthog from "posthog-js";
// Socket
import { ACTIVE_EXPERIMENTS, ACTIVE_GAMES, DEV_TOOLS } from "@/constants.ts";
import { useAppConfig } from "@/store/app.ts";
import logger from "@/services/logger.ts";
import { NetDriver } from "@/services/transport/netdriver.ts";
import { WebsocketGameService } from "@/services/game/WebsocketGameService.ts";
import { provideGameService } from "@/services/game/useGameService.ts";
import { usePuzzleMetadataStore } from "@/store/puzzle.ts";

if (import.meta.hot) {
  import.meta.hot.accept(["./constants.ts"], () => {
    import.meta.hot!.invalidate();
  });
}

StorageVersionManager.clearOldStorage(); // clear old storage if needed

const route = {
  view: (path: string, name: string, view: string) => ({
    path,
    name,
    component: () => import(`@/views/${view}.vue`),
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
    component: () => import("@/components/Freeplay.vue"),
    meta: { game_type: name },
  }),
  dev: (key: string, meta: Object) => ({
    path: `/devtool/${key}`,
    name: `dev-${key}`,
    component: () => import(`@/views/dev/${key}.vue`),
    meta,
  }),
  experiment: (key: string) => ({
    path: `/experiment/${key}`,
    name: `experiment-${key}`,
    meta: { experiment_key: key },
    component: () => import(`@/features/prolific.experiments/${key}/ExperimentMain.vue`),
  }),
};

/** This is the global list of routes that are available in the app. */
const routerConfig: RouterOptions = {
  history: createWebHistory(),
  routes: [
    route.view("", "Home", "Home"),
    route.markdown("/about-us", "about-us", mdAbout),
    ...Object.values(DEV_TOOLS).map(({ key, meta }) => route.dev(key, meta)),
    ...Object.keys(ACTIVE_EXPERIMENTS).map(route.experiment),
    ...Object.keys(ACTIVE_GAMES).map(route.game),
    // ...Object.keys(DEV_TOOLS).map(route.dev),
    { path: "/:pathMatch(.*)*", name: "404", component: () => import("./views/404.vue") },
  ],
};

/** app initialization */
(async () => {
  logger.debug("Bootstrapping app...");
  const app = createApp(App).use(createPinia()).use(createRouter(routerConfig)).component("v-icon", OhVueIcon);
  // attempt to get both: the backend should know.
  // if the user is logged in, the visitor ID is not distributed.
  // if there is no user, the visitor ID is used to identify the user
  await useAuthStore().updateStore();
  await useVisitorStore().init();
  await usePuzzleMetadataStore().refreshAllVariantsOnce();

  // set app mode (freeplay, prolific)
  const cfg = useAppConfig();
  cfg.setMode(detectModeFromPath());

  // app socket
  const gs = provideGameService();
  app.provide("GameService", gs);

  // posthog
  const posthogApiKey = import.meta.env.VITE_POSTHOG_API_KEY;
  const posthogApiHost = import.meta.env.VITE_POSTHOG_API_HOST || "https://app.posthog.com";
  if (posthogApiKey) {
    posthog.init(posthogApiKey, {
      api_host: posthogApiHost,
      loaded: (posthog) => {
        if (import.meta.env.DEV) posthog.debug();
      },
    });
    app.provide("posthog", posthog);
  } else {
    if (import.meta.env.DEV) {
      console.warn("PostHog API key (VITE_POSTHOG_API_KEY) is not set. PostHog will not be initialized.");
    }
  }
  app.mount("#app");
})();
