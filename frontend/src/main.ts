import { createApp } from "vue";
import { createPinia } from "pinia";
import { createRouter, createWebHistory, type RouterOptions } from "vue-router";
import App from "./App.vue";
import "./style.css";

/**
 * This is the global list of games that are available in the app.
 * The "key" is used to identify the game in the URL, in the local storage, and anywhere else
 * that we need to reference the game. Make sure there are no duplicates!
 */
export const ACTIVE_GAMES = [
  { name: "💣 Minesweeper", key: "minesweeper", badge: "New" },
  { name: "🧩 Sudoku", key: "sudoku", badge: "New" },
  { name: "⛺ Tents", key: "tents", badge: "WIP", badgeColor: "badge-warning" },
  // { name: "⬛ Kakurasu", key: "kakurasu", badge: "WIP", badgeColor: 'badge-warning' },
];

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
    component: () => import(`./components/views/${comp}.vue`),
  };
};

const game = (name: string) => {
  return {
    path: `/${name}`,
    name: `game-${name}`,
    component: () => import(`./components/games/${name}/${name}.freeplay.vue`),
    meta: { game_type: name },
  };
};

const routerConfig: RouterOptions = {
  history: createWebHistory(),
  routes: [
    path("", "Home", "Home"),
    path("/about-us", "about-us", "AboutUs"),
    ...ACTIVE_GAMES.map((gameObj) => game(gameObj.key)),
    { path: "/:pathMatch(.*)*", name: "404", component: () => import("./components/views/404.vue") },
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
} from "oh-vue-icons/icons";

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
);

createApp(App).use(createPinia()).use(createRouter(routerConfig)).component("v-icon", OhVueIcon).mount("#app");
