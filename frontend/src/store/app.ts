import { defineStore } from "pinia";

type AppMode = "freeplay" | "prolific";

export const useAppConfig = defineStore("mitlogic.appconfig", {
  state: () => ({
    mode: "freeplay" as AppMode,
  }),
  getters: {
    isProlific: (state) => state.mode === "prolific",
    isFreeplay: (state) => state.mode === "freeplay",
  },
  actions: {
    setMode(m: AppMode) {
      this.mode = m;
    },
  },
});
