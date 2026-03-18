import { defineStore } from "pinia";
import posthog from "posthog-js";
import { useAppStore } from "./useAppStore.ts";
import { api } from "@/core/services/client";
import { capture_error } from "@/core/services/posthog.ts";
import { i18next } from "@/i18n.ts";

export interface User {
  id: string;
  email: string;
  is_active: boolean;
  is_superuser: boolean;
  is_verified: boolean;
  username: string | null;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface RegisterPayload {
  email: string;
  password: string;
  username: string;
}

interface SocialLoginResponse {
  authorization_url: string;
}

export const useAuthStore = defineStore("auth", {
  state: () => ({
    user: null as User | null,
    loading: false,
    error: null as string | null,
    errorReason: null as string | null,
  }),
  
  getters: {
    isAuthenticated: (state) => !!state.user,
    isAdmin: (state) => !!state.user?.is_superuser,
    needsUsername: (state) => !!state.user && !state.user.username,
  },
  
  actions: {
    async fetchCurrentUser() {
      this.loading = true;
      this.error = null;

      const { data, error, response } = await api.GET("/api/users/me");
      this.loading = false;

      if (error) {
        if (response.status === 401) {
          this.user = null;
        } else {
          this.error = (error as any)?.detail || "Failed to fetch user";
          capture_error("fetch_current_user_failed", error);
        }
        return null;
      }

      this.user = data as User;
      const appStore = useAppStore();
      posthog.identify(this.user?.id, {
        email: this.user?.email,
        username: this.user?.username,
        last_login: new Date(),
        device_id: appStore.device_id,
      });
      return this.user;
    },

    async login(credentials: LoginPayload) {
      this.loading = true;
      this.error = null;

      const { error, response } = await api.POST("/api/auth/login", {
        body: { username: credentials.email, password: credentials.password },
        bodySerializer: (body) => new URLSearchParams(body as Record<string, string>),
      });

      if (error) {
        this.error = (error as any)?.detail || "Login failed";
        this.loading = false;
        return null;
      }

      await this.fetchCurrentUser();
      this.loading = false;
      return this.user;
    },

    async register(userData: RegisterPayload) {
      this.loading = true;
      this.error = null;

      const { data, error } = await api.POST("/api/auth/register", { body: userData });
      this.loading = false;

      if (error) {
        this.error = (error as any)?.detail || "Registration failed";
        capture_error("registration_failed", error);
        return null;
      }

      return data;
    },

    async verifyEmail(token: string) {
      const { error } = await api.POST("/api/auth/verify", { body: { token } });
      if (error) {
        this.error = (error as any)?.detail;
        return false;
      }

      posthog.capture('email_verified', { user_id: this.user?.id, email: this.user?.email });
      return true;
    },

    async resend_verification_email() {
      this.loading = true;
      this.error = null;

      const { error, response } = await api.POST("/api/auth/request-verify-token");
      this.loading = false;

      if (error) {
        this.error = response.status === 429
          ? i18next.t("auth:verification.error_rate_limit")
          : (error as any)?.detail || i18next.t("auth:verification.error_failed");
        return false;
      }
      return true;
    },

    async logout() {
      this.loading = true;
      await api.POST("/api/auth/logout");
      posthog.reset();
      this.user = null;
      this.error = null;
      this.loading = false;
    },

    async social_login(provider: string) {
      const { data, error } = await api.GET("/api/oauth/{provider}/authorize", {
        params: { path: { provider } },
      });
      if (error) {
        this.error = (error as any)?.detail || "Social login failed";
        return;
      }
      window.location.href = (data as SocialLoginResponse).authorization_url;
    },

    clearError() {
      this.error = null;
    },

    async initializeAuth() {
      await this.fetchCurrentUser();
    },

    async updateUsername(username: string) {
      this.loading = true;
      this.error = null;

      const { data, error } = await api.PATCH("/api/users/me", { body: { username } });
      this.loading = false;

      if (error) {
        this.error = (error as any)?.detail || "Failed to update username";
        return null;
      }

      this.user = data as User;
      return this.user;
    },

    async update_password(current_password: string, new_password: string) {
      this.loading = true;
      this.error = null;

      const { data, error } = await api.PATCH("/api/users/me", {
        body: { password: new_password, current_password },
      });
      this.loading = false;

      if (error) {
        this.error = (error as any)?.detail || "Failed to update password";
        return null;
      }

      this.user = data as User;
      return this.user;
    },
  },
});
