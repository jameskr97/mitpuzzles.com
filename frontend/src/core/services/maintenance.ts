import { createApp } from "vue";
import { I18NextVue, i18next } from "@/i18n.ts";

export async function check_maintenance_mode(): Promise<boolean> {
  try {
    const response = await fetch("/maintenance.json");
    if (response.ok) {
      const maintenance_data = await response.json();
      const { default: MaintenanceMode } = await import("@/core/components/MaintenanceMode.vue");
      const maintenance_app = createApp(MaintenanceMode, {
        reason: maintenance_data.reason || null,
      }).use(I18NextVue, { i18next });
      maintenance_app.mount("#app");
      return true;
    }
  } catch {
    // 404 or network error - maintenance mode is OFF
  }
  return false;
}
