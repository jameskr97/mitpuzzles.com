import { createRouter, createWebHistory } from "vue-router";
import { routes } from "./routes";

export const router = createRouter({
  history: createWebHistory(),
  routes,
});

export { setup_auth_guard, check_initial_route } from "./guards";
