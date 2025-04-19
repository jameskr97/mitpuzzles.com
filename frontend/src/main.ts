import { createApp, defineAsyncComponent } from "vue";
import { createPinia } from "pinia";
import { createRouter, createWebHistory, type RouterOptions } from "vue-router";
import * as adapter from "@/store/adapters";
import App from "./App.vue";
import "./style.css";
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
    path("/about-us", "about-us", "AboutUs"),
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
} from "oh-vue-icons/icons";
import { defaultPuzzles } from "@/services/puzzle.defaults.ts";
import { StorageVersionManager } from "@/utils.ts";
import type { PuzzleAdapter } from "@/store/adapters";

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
);

createApp(App).use(createPinia()).use(createRouter(routerConfig)).component("v-icon", OhVueIcon).mount("#app");
