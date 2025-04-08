import { defineStore } from "pinia";
import * as app from "@/services/app";

export const useAppConfig = defineStore("app_config", {
  state: () => ({
    games: null as unknown,
  }),
  actions: {
    async fetchGameSettings() {
      if (this.games !== null) return;
      this.games = await app.getAppSettings();
    },
  },
});
