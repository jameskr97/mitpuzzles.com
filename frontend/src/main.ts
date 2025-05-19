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
import { usePuzzleSocket } from "@/features/games.composables/usePuzzleSocket.ts";
import { defaultPuzzles } from "@/services/puzzle.defaults.ts";
// Markdown content
import mdAbout from "./views/aboutus.md?raw";
// Utility
import { StorageVersionManager } from "@/utils.ts";
// Style
import "./style.css";

StorageVersionManager.clearOldStorage(); // clear old storage if needed

/** Puzzle Components */
function create_game_entry(sidebar_title: string, key: string) {
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
  sudoku:       create_game_entry("🧩 Sudoku", "sudoku"),
  tents:        create_game_entry("⛺ Tents", "tents"),
  kakurasu:     create_game_entry("⬛ Kakurasu", "kakurasu"),
  lightup:      create_game_entry("💡 Light Up", "lightup"),
  // battleship:   create_game_entry("🚢 Battleship", "battleship"),
  // nonograms:    create_game_entry("🖼️ Nonograms", "nonograms"),
}
export type GameKey = keyof typeof ACTIVE_GAMES;

function create_dev_tool(key: string, display_name: string) {
  return {
    key,
    name: display_name,
    component: `./views/dev/${key}.vue`,
  };
}
export const DEV_TOOLS: Record<string, any> = {
  "test-board": create_dev_tool("test-board", "🎯 Test Board"),
  "test-websocket": create_dev_tool("test-websocket", "🧦 Test Websockets"),
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
  dev: (name: string) => ({
    path: `/devtool/${name}`,
    name: `dev-${name}`,
    component: () => import(`${DEV_TOOLS[name].component}`),
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

  const puzzle_socket = usePuzzleSocket();
  app.provide("puzzle_socket", puzzle_socket);
  // attempt to get both: the backend should know.
  // if the user is logged in, the visitor ID is not distributed.
  // if there is no user, the visitor ID is used to identify the user
  await useAuthStore().updateStore();
  await useVisitorStore().init();
  app.mount("#app");
})();
