import { defineStore } from "pinia";
import * as api from "@/services/app";

export interface InitVisitorResponse {
  visitor_id: string;
}

export const useVisitorStore = defineStore("visitor", {
  state: () => ({
    initialized: false as boolean,
    visitor_id: null as string | null,
  }),
  actions: {
    /**
     * Call your backend’s /api/visitor endpoint exactly once
     * to get/set the HttpOnly cookie and (optionally) grab the ID.
     */
    async init() {
      if (this.initialized) return;
      try {
        const res = await api.ensureVisitor();
        if (res.status === 201) {
          // If 201, we got a new visitor ID
          this.visitor_id = (res.data as InitVisitorResponse).visitor_id;
        }
        // if 204, the cookie was already present & valid
        this.initialized = true;
      } catch {}
    },
  },
});
