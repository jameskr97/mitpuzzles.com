import { defineStore } from "pinia";
import * as api from "@/services/app";
import { useLocalStorage } from "@vueuse/core";
import type { AxiosError, AxiosResponse } from "axios";

export interface InitVisitorResponse {
  visitor_id: string;
}

export const useVisitorStore = defineStore("visitor", {
  state: () => ({
    initialized: false as boolean,
    generated_username: "" as string,
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
        if (res.status === 201 || res.status === 200) {
          this.generated_username = res.data.generated_username;
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


    async changeUsername(new_username: string) {
      if (!this.initialized) {
        console.warn("Visitor store not initialized, cannot change username");
        return;
      }
      return api.changeVisitorUsername(new_username)
        .then((res: AxiosResponse) => {
          this.generated_username = new_username
          return {"changed": true, "username": new_username };
        })
        .catch((err: AxiosError) => {
          return {"changed": false, "error": err.response?.data?.error || "Unknown error"};
        })
      // try {
      //   const res = await api.changeVisitorUsername(new_username);
      //   if (res.status === 200) {
      //     this.generated_username = new_username;
      //     return { "username": new_username, changed: true };
      //   }
      //
      //   if (res.status === 400) {
      //     return { changed: false, error: res.data.error };
      //   }
      // } catch (err: any) {
      //   return { changed: false, error: err.response.data.error };
      // }
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
