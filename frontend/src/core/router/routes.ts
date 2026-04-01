import type { RouteRecordRaw } from "vue-router";
import { route } from "./helpers";
import { ACTIVE_GAMES, ADMIN_TOOLS } from "@/constants.ts";
import ExperimentRunner from "@/features/experiment-core/components/ExperimentRunner.vue";

export const routes: RouteRecordRaw[] = [
  route.view("", "Home", "Home"),
  ...Object.values(ADMIN_TOOLS).map((tool) => route.admin(tool.route_path, tool.key, tool.key)),
  route.admin("/admin/playback/:attempt_id", "playback", "playback"),
  route.admin("/admin/dashboard", "dashboard", "Dashboard"),
  route.admin("/admin/puzzle/:puzzle_id", "puzzle-detail", "PuzzleDetail"),
  route.view("/signup", "signup", "Signup", false),
  route.view("/verify-email", "verify-email", "SignupVerifyEmail", false),
  route.view("/reset-password", "reset-password", "ResetPassword", false),
  route.view("/account", "account", "AccountSettings", true, true),
  route.view("/@/:username", "user-profile", "UserProfile"),
  route.view("/leaderboard", "leaderboard", "Leaderboard"),
  route.view("/game/:attempt_id", "game-playback", "GamePlayback"),
  route.view("/about-us", "about-us", "AboutUs"),
  route.view("/privacy-policy", "privacy-policy", "privacy-policy"),
  route.view("/board2", "board2", "board2"),
  route.view("/daily", "game-daily", "DailyPuzzle"),
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
  { path: "/:pathMatch(.*)*", name: "404", component: () => import("@/views/404.vue") },
];
