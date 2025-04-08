import { defineStore } from "pinia";
import * as allauth from "@/services/allauth";

/* We allow the user to login with either an email or a username */
export interface LoginPayload {
  email?: string;
  username?: string;
  password: string;
}

interface AllAuthUser {
  id: number;
  display: string;
  email: string;
  username: string;
}

export const useAuthStore = defineStore("auth", {
  state: () => ({
    auth_config: null as Object | null,
    user: null as AllAuthUser | null,
  }),
  getters: {
    config: (state) => state.auth_config,
    isAuthenticated: (state) => !!state.user,
  },
  actions: {
    async signup(data: allauth.AuthInfo): Promise<AllAuthUser> {
      const res = await allauth.signup(data);

      // Account Create Success - Store User
      if (res.status == 200) {
        this.user = res.data.user;
        return res.data.user;
      }

      // We have a list of errors. Transform, and return to user.
      if (res.status == 400) {
        // Group error messages by the 'param' field.
        throw allauth.aggregateErrorMessages(res.errors);
      }

      throw res;
    },

    /**
     * Attemt to login and store user information
     * @param data The user info to login with
     */
    async login(data: LoginPayload) {
      const res = await allauth.login(data);
      if (res.status === 200) {
        this.user = res.data.user;
      } else if (res.status === 400) {
        throw allauth.aggregateErrorMessages(res.errors);
      }
      // Note: key is "password", because the UI will communicate this to
      // `form.dynamic.vertical.vue`, and will display errors with the associated
      // input field, which in this case, is the password field.
      throw { password: "An unknown error occured" };
    },

    /* Delete current session, remove local auth user data */
    async logout() {
      await allauth.logout();
      this.user = null;
    },

    /**
     * Fetch the current user-info
     * @returns True if store modified, otherwise, false
     */
    async updateStore() {
      if (this.isAuthenticated) return false;

      try {
        const user = await allauth.getSession();
        this.user = user.data.user;
        return true;
      } catch {}
    },
  },
});
