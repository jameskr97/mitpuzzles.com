import { createApp } from "vue";
import { createPinia } from "pinia";
import App from "./App.vue";
import { OhVueIcon } from "@/icons";
import { I18NextVue, i18next } from "@/i18n.ts";
import { StorageVersionManager } from "@/utils.ts";
import logger from "@/core/services/logger.ts";
import "./style.css";
import 'overlayscrollbars/overlayscrollbars.css';

// Router
import { router, setup_auth_guard, check_initial_route } from "@/core/router";

// Services
import { register_pwa } from "@/core/services/pwa.ts";
import { init_posthog } from "@/core/services/posthog.ts";
import { check_maintenance_mode } from "@/core/services/maintenance.ts";

// Store initialization
import { init_app_store, init_session_tracking, init_auth, init_puzzle_stores } from "@/core/store/init.ts";

// HMR support
if (import.meta.hot) {
  import.meta.hot.accept(["./constants.ts"], () => {
    import.meta.hot!.invalidate();
  });
}

// App initialization
(async () => {
  // Clear old storage if version changed (must be awaited before store init)
  await StorageVersionManager.clearOldStorage();

  // Check for maintenance mode before initializing
  if (await check_maintenance_mode()) return;

  logger.debug("Bootstrapping app...");
  register_pwa();

  const app = createApp(App)
    .use(createPinia())
    .use(router)
    .use(I18NextVue, { i18next })
    .component("v-icon", OhVueIcon);

  // Initialize stores
  await init_app_store();
  await init_session_tracking();
  init_posthog(app);

  // Initialize auth and set up router guards
  await init_auth();
  await check_initial_route(router);
  setup_auth_guard(router);

  // Initialize puzzle stores and mount
  await init_puzzle_stores();
  app.mount("#app");
})();
