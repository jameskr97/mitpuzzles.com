import { registerSW } from "virtual:pwa-register";
import { createLogger } from "@/core/services/logger.ts";
const log = createLogger("pwa");

export function register_pwa() {
  registerSW({
    onNeedRefresh() {
      log("Service worker needs refresh");
    },
    onOfflineReady() {
      log("App ready to work offline");
    },
  });
}
