import { defineStore } from "pinia";
import axios, { type AxiosResponse } from "axios";
import posthog from "posthog-js";
import { useAppStore } from "./useAppStore.ts";

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
      
      try {
        const response = await axios.get("/api/users/me");
        this.user = response.data;
        // identify user to posthog
        const appStore = useAppStore();
        posthog.identify(this.user?.id,
          {
            email: this.user?.email,
            username: this.user?.username,
            last_login: new Date(),
            device_id: appStore.device_id,
          })

        return this.user;
      } catch (error: any) {
        if (error.response?.status === 401) {
          this.user = null;
        } else {
          this.error = error.response?.data?.detail || "Failed to fetch user";
        }
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async login(credentials: LoginPayload) {
      this.loading = true;
      this.error = null;
      
      try {
        const formData = new FormData();
        formData.append("username", credentials.email);
        formData.append("password", credentials.password);
        
        await axios.post("/api/auth/login", formData, {
          headers: {
            "Content-Type": "application/x-www-form-urlencoded",
          },
        });
        await this.fetchCurrentUser(); // After successful login, fetch user data
        return this.user;
      } catch (error: any) {
        this.error = error.response?.data?.detail || "Login failed";
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async register(userData: RegisterPayload): Promise<AxiosResponse> {
      this.loading = true;
      this.error = null;
      
      try {
        return await axios.post("/api/auth/register", userData);
      } catch (error: any) {
        this.error = error.response?.data?.detail || "Registration failed";
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async verifyEmail(token: string) {
      try {
        await axios.post("/api/auth/verify", {token});
        // track email verification with posthog
        posthog.capture('email_verified',
          { user_id: this.user?.id, email: this.user?.email }
        );
      } catch (error: any) {
        this.error = error.response?.data?.detail;
        throw error;
      }
    },

    async resend_verification_email() {
      this.loading = true;
      this.error = null;

      try {
        await axios.post("/api/auth/request-verify-token");
        return { success: true };
      } catch (error: any) {
        this.error = error.response?.data?.detail || "Failed to resend verification email";
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async logout() {
      this.loading = true;
      
      try {
        await axios.post("/api/auth/logout");
        posthog.reset()
      } catch (error) {
        // Even if logout fails on server, clear local state
        console.warn("Logout request failed:", error);
      } finally {
        this.user = null;
        this.error = null;
        this.loading = false;
      }
    },

    async social_login(provider: string) {
      try {
        const response = await axios.get<SocialLoginResponse>(`/api/oauth/${provider}/authorize`);
        window.location.href = response.data.authorization_url;

      } catch (error: any) {
        this.error = error.response?.data?.detail || "Social login failed";
        throw error;
      }
    },

    clearError() {
      this.error = null;
    },

    async initializeAuth() {
      try {
        await this.fetchCurrentUser();
      } catch (error) {} // User not authenticated, which is fine
    },

    async updateUsername(username: string) {
      this.loading = true;
      this.error = null;

      try {
        const response = await axios.patch("/api/users/me", { username });
        this.user = response.data;
        return this.user;
      } catch (error: any) {
        this.error = error.response?.data?.detail || "Failed to update username";
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async update_password(current_password: string, new_password: string) {
      this.loading = true;
      this.error = null;

      try {
        const response = await axios.patch("/api/users/me", {
          password: new_password,
          current_password: current_password
        });
        this.user = response.data;
        return this.user;
      } catch (error: any) {
        this.error = error.response?.data?.detail || "Failed to update password";
        throw error;
      } finally {
        this.loading = false;
      }
    },
  },
});
