import { defineStore } from "pinia"
import * as app from "@/api/app";


export const useAppConfig = defineStore('app_config', {
    state: () => ({
        games: null as unknown as app.GameSettings,
    }),
    actions: {
        async fetchGameSettings() {
            if (this.games !== null) return;
            this.games = await app.getAppSettings();
        }
    }
})