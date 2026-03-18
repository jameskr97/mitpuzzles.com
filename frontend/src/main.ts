import { createApp } from "vue";
import { createPinia } from "pinia";
import App from "./App.vue";
import { OhVueIcon } from "@/icons";
import { I18NextVue, i18next } from "@/i18n.ts";
import { StorageVersionManager } from "@/utils.ts";
import { createLogger } from "@/core/services/logger.ts";
const log = createLogger("main");
import "./style.css";
import 'overlayscrollbars/overlayscrollbars.css';
import { useAppStore} from "@/core/store/useAppStore.ts";

// Router
import { router, setup_auth_guard, check_initial_route } from "@/core/router";

// Services
import { register_pwa } from "@/core/services/pwa.ts";
import { init_posthog, posthog_error_handler } from "@/core/services/posthog.ts";
import { check_maintenance_mode } from "@/core/services/maintenance.ts";
import { watch } from "vue";

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

  log("Bootstrapping app...");
  register_pwa();


  const app = createApp(App)
    .use(createPinia())
    .use(router)
    .use(I18NextVue, { i18next })
    .component("v-icon", OhVueIcon);
  app.config.errorHandler = posthog_error_handler;
  app.mount("#app");

  init_app_store();
  init_session_tracking();
  init_puzzle_stores();

  // following three lines must happen in this order (each dependent on the last)
  await init_auth();
  setup_auth_guard(router);
  await check_initial_route(router);

  // gate posthog behind privacy consent
  const appStore = useAppStore();
  if (appStore.has_consented) {
    init_posthog(app);
  } else {
    watch(() => appStore.has_consented, (v) => { if (v) init_posthog(app); }, { once: true });
  }

})();
