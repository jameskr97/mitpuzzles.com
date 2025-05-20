import { defineStore } from "pinia";
import * as api from "@/services/app";
import { useLocalStorage } from "@vueuse/core";

export interface InitVisitorResponse {
  visitor_id: string;
}

export const useVisitorStore = defineStore("visitor", {
  state: () => ({
    initialized: false as boolean,
    accepted_cookies: useLocalStorage("accepted_cookies", false),
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
        if (res.status === 201 || res.status === 204) {
          // 201 Created: Visitor ID was created
          // 204 No Content: Visitor ID already exists
          this.initialized = true;
        } else {
          console.error("Unexpected response from /api/visitor", res);
        }
      } catch (err) {
        console.error("Failed to initialize visitor store", err);
      }
    },

    /**
     * Set the cookie consent flag in the backend
     * @param accepted Whether the user accepted cookies
     */
    async setCookieConsent(accepted: boolean) {
      this.accepted_cookies = accepted;
    },
  },
});
