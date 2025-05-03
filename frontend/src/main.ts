import { createApp, defineAsyncComponent, h } from "vue";
import { createPinia } from "pinia";
import { createRouter, createWebHistory, type RouterOptions } from "vue-router";
import * as adapter from "@/store/adapters";
import App from "./App.vue";
import "./style.css";
// markdown pages
import mdAbout from "./views/aboutus.md?raw";

StorageVersionManager.clearOldStorage(); // clear old storage if needed

/** Puzzle Components */
function create_game_entry<Raw, State>(sidebar_title: string, key: string, adapter: PuzzleAdapter<Raw, State>) {
  return {
    key,
    name: sidebar_title,
    component: defineAsyncComponent({ loader: () => import(`@/features/games/${key}/${key}.puzzle.vue`) }),
    instructions: async () => await import(`@/features/games/${key}/instructions.md?raw`),
    adapter,
    default: async () => adapter.create_state(defaultPuzzles[key]),
  };
}

/**
 * This is the global list of games that are available in the app.
 * The "key" is used to identify the game in the URL, in the local storage, and anywhere else
 * that we need to reference the game's data. Make sure there are no duplicates!
 */
/* prettier-ignore */
export const ACTIVE_GAMES: Record<string, any> = {
  minesweeper:  create_game_entry("💣 Minesweeper", "minesweeper", adapter.minesweeperAdapter),
  sudoku:       create_game_entry("🧩 Sudoku", "sudoku", adapter.sudokuAdapter),
  tents:        create_game_entry("⛺ Tents", "tents", adapter.tentsAdapter),
  kakurasu:     create_game_entry("⬛ Kakurasu", "kakurasu", adapter.kakurasuAdapter),
  lightup:      create_game_entry("💡 Light Up", "lightup", adapter.lightupAdapter),
}

/**
 * This is the type of the keys in the ACTIVE_GAMES object.
 * Used in type definitions to ensure that when a game is added or removed,
 * from the ACTIVE_GAMES object, the type system will catch it in other
 * parts of the codebase.
 */
export type GameKey = keyof typeof ACTIVE_GAMES;

/**
 * Function to help with generating path dictinary that will be used in routerConfig
 * @param path the path for this view
 * @param name the path name (for referencing in other functions)
 * @param comp the component to be displayed at this endpoint
 * @returns a routerConfig
 */
const path = (path: string, name: string, comp: string) => {
  return {
    path: path,
    name: name,
    component: () => import(`./views/${comp}.vue`),
  };
};

function markdown(path: string, name: string, mdContent: string, proseClass = "prose-lg") {
  return {
    path,
    name,
    component: {
      render() {
        return h(MarkdownPage, {
          content: mdContent,
          proseClass,
        });
      },
    },
  };
}

const game = (name: string) => {
  return {
    path: `/${name}`,
    name: `game-${name}`,
    // component: () => import(`./features/games/${name}/${name}.freeplay.vue`),
    component: () => import("./components/Freeplay.vue"),
    // freeplay: () => import(`./features/games/${name}/${name}.freeplay.vue`),
    meta: { game_type: name },
  };
};

const routerConfig: RouterOptions = {
  history: createWebHistory(),
  routes: [
    path("", "Home", "Home"),
    markdown("/about-us", "about-us", mdAbout),
    ...Object.keys(ACTIVE_GAMES).map((gamekey) => game(gamekey)),
    { path: "/:pathMatch(.*)*", name: "404", component: () => import("./views/404.vue") },
  ],
};

////////////////////////////////////////////////////////////////////////////////
// Add OhVueIcons (https://oh-vue-icons.js.org/)
import { OhVueIcon, addIcons } from "oh-vue-icons";
import {
  FaUndoAlt,
  FaRedoAlt,
  IoCloseSharp,
  HiCheck,
  MdFibernew,
  FaCheckCircle,
  IoClose,
  HiInformationCircle,
  MdLeaderboard,
  BiLightbulbFill,
  MdArrowdropdown
} from "oh-vue-icons/icons";
import { defaultPuzzles } from "@/services/puzzle.defaults.ts";
import { StorageVersionManager } from "@/utils.ts";
import type { PuzzleAdapter } from "@/store/adapters";
import { useAuthStore } from "@/store/auth.ts";
import { useVisitorStore } from "@/store/visitor.ts";
import MarkdownPage from "@/views/MarkdownPage.vue";

addIcons(
  FaUndoAlt,
  FaRedoAlt,
  IoCloseSharp,
  HiCheck,
  MdFibernew,
  FaCheckCircle,
  IoClose,
  HiInformationCircle,
  MdLeaderboard,
  BiLightbulbFill,
  MdArrowdropdown
);

(async () => {
  const app = createApp(App)
    .use(createPinia())
    .use(createRouter(routerConfig))
    .component("v-icon", OhVueIcon);

  // attempt to get current user.
  const auth = useAuthStore();
  await auth.updateStore();

  // attempt to get the visitor id.
  const visitor = useVisitorStore();
  await visitor.init();
  // both user and visitor stores are attempted, though the backend knows that:
  // if the user is logged in, the visitor ID is not distributed.
  // if there is no user, the visitor ID is used to identify the user

  app.mount("#app");
})();
