import { h } from "vue";
import MarkdownPage from "@/views/MarkdownPage.vue";
import { ACTIVE_GAMES } from "@/constants.ts";

export const route = {
  view: (path: string, name: string, view: string, sidebar: boolean = true, require_logged_in: boolean = false) => ({
    path,
    name,
    component: () => import(`@/views/${view}.vue`),
    meta: { showSidebar: sidebar, requireLoggedIn: require_logged_in },
  }),

  admin: (path: string, name: string, view: string, sidebar: boolean = true) => ({
    path,
    name,
    component: () => import(`@/views/${view}.vue`),
    meta: { showSidebar: sidebar, requiresAdmin: true },
  }),

  markdown: (path: string, name: string, content: string, prose_class = "prose-lg") => ({
    path,
    name,
    component: {
      render: () => h(MarkdownPage, { content, proseClass: prose_class }),
    },
  }),

  game: (name: string) => ({
    path: `/${name}`,
    name: `game-${name}`,
    component: ACTIVE_GAMES[name].freeplay,
    meta: { game_type: name },
  }),

  dev: (key: string, meta: object) => ({
    path: `/devtool/${key}`,
    name: `dev-${key}`,
    component: () => import(`@/views/dev/${key}.vue`),
    meta: { ...meta, requiresAdmin: true },
  }),
};
