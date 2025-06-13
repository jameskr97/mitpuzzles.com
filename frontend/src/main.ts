// Vue core
import { createApp, defineAsyncComponent, h } from "vue";
import { createRouter, createWebHistory, type RouterOptions } from "vue-router";
// Pinia store
import { createPinia } from "pinia";
import { useAuthStore } from "@/store/auth.ts";
import { useVisitorStore } from "@/store/visitor.ts";
// Components & Views
import App from "./App.vue";
import MarkdownPage from "@/views/MarkdownPage.vue";
import { OhVueIcon } from "@/icons";
import { defaultPuzzles } from "@/services/puzzle.defaults.ts";
// Markdown content
import mdAbout from "./views/aboutus.md?raw";
// Utility
import { StorageVersionManager } from "@/utils.ts";
// Style
import "./style.css";
// PostHog
import posthog from "posthog-js";
import { withSudokuBehaviors } from "@/features/games/sudoku/useSudokuCellHighlighter.ts";
import { withSudokuFocusBehavior } from "@/features/games/sudoku/useSudokuFocusHighlighter.ts";
import { ModuleManager } from "@/services/eventbus.ts";
import { websocketModule } from "@/services/eventbus.modules/websocket.ts";
import { debugModule } from "@/services/eventbus.modules/debug.ts";
import { gameModule } from "@/services/eventbus.modules/game.ts";

StorageVersionManager.clearOldStorage(); // clear old storage if needed

/** Puzzle Components */
function create_game_entry(sidebar_title: string, key: string, defaultBehaviors: Array<any> = []) {
  return {
    key,
    name: sidebar_title,
    component: defineAsyncComponent({ loader: () => import(`@/features/games/${key}/${key}.puzzle.vue`) }),
    instructions: async () => {
      try {
        return await import(`@/features/games/${key}/instructions.md?raw`);
      } catch (e) {
        if (import.meta.env.DEV) {
          return { default: "# No instructions yet\n_Add instructions.md to this game folder._" };
        } else {
          throw e;
        }
      }
    },
    default: defaultPuzzles[key],
    defaultBehaviors,
  };
}

/**
 * This is the global list of games that are available in the app.
 * The "key" is used to identify the game in the URL, in the local storage, and anywhere else
 * that we need to reference the game's data. Make sure there are no duplicates!
 */
/* prettier-ignore */
export const ACTIVE_GAMES: Record<string, any> = {
  minesweeper:  create_game_entry("💣 Minesweeper", "minesweeper"),
  sudoku:       create_game_entry("🧩 Sudoku", "sudoku", [withSudokuBehaviors, withSudokuFocusBehavior]),
  tents:        create_game_entry("⛺ Tents", "tents"),
  kakurasu:     create_game_entry("⬛ Kakurasu", "kakurasu"),
  lightup:      create_game_entry("💡 Light Up", "lightup"),
  // battleship:   create_game_entry("🚢 Battleship", "battleship"),
  // nonograms:    create_game_entry("🖼️ Nonograms", "nonograms"),
}
export type GameKey = keyof typeof ACTIVE_GAMES;

function create_dev_tool(key: string, display_name: string, requires_admin: boolean = false) {
  return {
    key,
    name: display_name,
    component: import(`@/views/dev/${key}.vue`),
    requires_admin,
  };
}
export const DEV_TOOLS: Record<string, any> = {
  "test-board": create_dev_tool("test-board", "🎯 Test Board"),
  "test-websocket": create_dev_tool("test-websocket", "🧦 Test Websockets"),
  // "test-monitor": create_dev_tool("test-monitor", "🖥️ Test Monitor", true),
  // "test-experiment": create_dev_tool("test-experiment", "📝 Text Experiment"),
};

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
  dev: (key: string) => ({
    path: `/devtool/${key}`,
    name: `dev-${key}`,
    component: () => import(`@/views/dev/${key}.vue`),
  }),
};

/** This is the global list of routes that are available in the app. */
const routerConfig: RouterOptions = {
  history: createWebHistory(),
  routes: [
    route.view("", "Home", "Home"),
    route.markdown("/about-us", "about-us", mdAbout),
    ...Object.keys(ACTIVE_GAMES).map(route.game),
    ...Object.keys(DEV_TOOLS).map(route.dev),
    { path: "/:pathMatch(.*)*", name: "404", component: () => import("./views/404.vue") },
  ],
};

/** app initialization */
(async () => {
  const app = createApp(App).use(createPinia()).use(createRouter(routerConfig)).component("v-icon", OhVueIcon);
  // attempt to get both: the backend should know.
  // if the user is logged in, the visitor ID is not distributed.
  // if there is no user, the visitor ID is used to identify the user
  await useAuthStore().updateStore();
  await useVisitorStore().init();

  // init event bus modules
  const event_modules = new ModuleManager();
  // event_modules.register(debugModule);
  event_modules.register(websocketModule);
  event_modules.register(gameModule);
  app.provide("event_modules", event_modules);

  // const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  // const url = `${protocol}://${window.location.host}/ws/puzzle/`;
  // const socket = new AppSocket(url, import.meta.env.DEV)
  // app.provide("socket", socket);

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
