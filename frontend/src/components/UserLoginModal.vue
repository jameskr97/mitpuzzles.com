<script setup lang="ts">
import { ref, computed } from "vue";
import { useRouter } from "vue-router";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuthStore } from "@/store/useAuthStore.ts";
import { useAppStore } from "@/store/useAppStore.ts";
import UserForgotPasswordModal from "@/components/UserForgotPasswordModal.vue";
import { useTranslation } from "i18next-vue";

const { t } = useTranslation();
const auth = useAuthStore();
const appStore = useAppStore();
const router = useRouter();

// Form fields
const email = ref("");
const password = ref("");
const forgot_password_modal_open = ref(false);

// Form validation
const isFormValid = computed(() => {
  return email.value && password.value && email.value.includes("@");
});

// Clear error when user starts typing
const clearErrorOnInput = () => {
  if (auth.error) {
    auth.clearError();
  }
};

// Computed property for display error message
const displayError = computed(() => {
  if (!auth.error) return null;
  if (auth.error === "LOGIN_BAD_CREDENTIALS") return t("auth:login.error_bad_credentials");
  return auth.error;
});

// Handle login submission
const handleLogin = async () => {
  if (!isFormValid.value) return;

  try {
    await auth.login({ email: email.value, password: password.value });
    // invariant - login success
    // Success - close modal and redirect
    appStore.close_login_modal(); // close modal
    email.value = ""; // reset form
    password.value = "";
    await router.push("/"); // redirect homepage
  } catch (error) {
    console.error("Login failed:", error);
  }
};

// Handle forgot password
const open_forgot_password = () => {
  forgot_password_modal_open.value = true;
};
</script>

<template>
  <Dialog v-model:open="appStore.login_modal_open">
    <DialogContent as-child>
      <Card class="mx-auto sm:max-w-[400px]">
        <CardHeader>
          <CardTitle class="text-2xl">{{ $t('auth:login.title') }}</CardTitle>
          <CardDescription>{{ $t('auth:login.description') }}</CardDescription>
        </CardHeader>
        <CardContent>
          <form @submit.prevent="handleLogin" class="grid gap-4">
            <!-- Email -->
            <div class="grid gap-2">
              <Label for="email">{{ $t('ui:form.email') }}</Label>
              <Input
                id="email"
                v-model="email"
                type="email"
                :placeholder="$t('ui:form.email')"
                required
                @input="clearErrorOnInput"
                :disabled="auth.loading"
              />
            </div>

            <!-- Password -->
            <div class="grid gap-2">
              <div class="flex items-center">
                <Label for="password">{{ $t('ui:form.password') }}</Label>
                <button
                  data-testid="link-forgot-password"
                  type="button"
                  @click="open_forgot_password"
                  class="ml-auto inline-block text-sm underline text-primary hover:text-primary/80"
                >
                  {{ $t('auth:login.forgot_password') }}
                </button>
              </div>
              <Input
                id="password"
                v-model="password"
                type="password"
                required
                @input="clearErrorOnInput"
                :disabled="auth.loading"
              />
            </div>

            <!-- Error Display -->
            <div v-if="displayError" data-testid="error-login-bad-credentials" class="text-sm text-red-600 bg-red-50 border border-red-200 rounded p-3">
              {{ displayError }}
            </div>

            <!-- Actions -->
            <Button data-testid="btn-login" type="submit" class="w-full" :disabled="!isFormValid || auth.loading">
              <div v-if="auth.loading" class="flex items-center gap-2">
                <div class="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin"></div>
                {{ $t('auth:login.logging_in') }}
              </div>
              <span v-else>{{ $t('ui:action.login') }}</span>
            </Button>
          </form>
          <Button data-testid="btn-google-login" variant="outline" class="w-full mt-2" :disabled="auth.loading" @click="auth.social_login('google')">
            <svg class="w-4 h-4 mr-2" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            {{ $t('auth:login.google_login') }}
          </Button>

          <div class="mt-4 text-center text-sm">
            <span class="mr-1">{{ $t('auth:login.no_account') }}</span>
            <router-link data-testid="link-signup" :to="{ name: 'signup' }" @click="appStore.close_login_modal()">
              <span class="underline">{{ $t('ui:action.signup') }}</span>
            </router-link>
          </div>
        </CardContent>
      </Card>
    </DialogContent>
  </Dialog>

  <!-- Forgot Password Modal -->
  <UserForgotPasswordModal v-model:open="forgot_password_modal_open" />
</template>
