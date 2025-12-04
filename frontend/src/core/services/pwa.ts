import { registerSW } from "virtual:pwa-register";
import logger from "@/core/services/logger.ts";

export function register_pwa() {
  registerSW({
    onNeedRefresh() {
      logger.debug("Service worker needs refresh");
    },
    onOfflineReady() {
      logger.debug("App ready to work offline");
    },
  });
}
