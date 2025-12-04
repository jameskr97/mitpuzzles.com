<script setup lang="ts">
import { Button } from "@/core/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/core/components/ui/card";
import { Input } from "@/core/components/ui/input";
import { Label } from "@/core/components/ui/label";
import { computed, ref } from "vue";
import { useAuthStore } from "@/core/store/useAuthStore.ts";
import { useAppStore } from "@/core/store/useAppStore.ts";
import { useRouter } from "vue-router";
import AppLogo from "@/core/components/AppLogo.vue";
import { useTranslation } from "i18next-vue";
import { Separator } from "@/core/components/ui/separator";

const { t } = useTranslation();

// Form Related Fields
const username = ref("");
const email = ref("");
const password = ref("");
const passwordVerify = ref("");
const router = useRouter();
const appStore = useAppStore();

const handle_signin_click = async () => {
  appStore.open_login_modal();
  await router.push("/");
};
const clearErrorOnInput = () => {
  if (authStore.error) {
    authStore.clearError();
  }
};
const emailError = computed(() => {
  if (!email.value) return "";
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email.value) ? "" : t("ui:validation.invalid_email");
});
const passwordMatchError = computed(() => {
  if (!password.value || !passwordVerify.value) return "";
  return password.value === passwordVerify.value ? "" : t("ui:validation.password_mismatch");
});
const isFormValid = computed(() => {
  return (
    username.value &&
    email.value &&
    !emailError.value &&
    password.value &&
    passwordVerify.value &&
    !passwordMatchError.value
  );
});

// Submission Field
const authStore = useAuthStore();
const submitForm = async () => {
  try {
    await authStore.register({ username: username.value, email: email.value, password: password.value });
    await authStore.login({ email: email.value, password: password.value });
    await router.push("/");
  } catch (error) {
    // Error is already stored in authStore.error
    console.error("Registration error:", error);
  }
};
</script>
<template>
  <div class="flex flex-col h-full w-full items-center justify-center p-4">
    <Card class="mx-auto md:w-[400px] w-full">
      <CardHeader class="text-center">
        <AppLogo class="w-80 mb-4 mx-auto" />
        <Separator />
        <CardTitle class="text-2xl">{{ $t('auth:signup.title') }}</CardTitle>
        <CardDescription>{{ $t('auth:signup.description') }}</CardDescription>
      </CardHeader>
      <CardContent>
        <form @submit.prevent="submitForm">
          <div class="grid gap-4">
            <!-- Username -->
            <div class="grid gap-2">
              <Label for="username">{{ $t('ui:form.username') }}</Label>
              <Input
                id="username"
                v-model="username"
                :placeholder="$t('ui:form.username')"
                autocomplete="username"
                required
                @input="clearErrorOnInput"
                :disabled="authStore.loading"
              />
            </div>

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
                :disabled="authStore.loading"
              />
              <div data-testid="error-invalid-email" v-if="emailError" class="text-sm text-red-600">{{ emailError }}</div>
            </div>

            <!-- Password -->
            <div class="grid gap-2">
              <Label for="password">{{ $t('ui:form.password') }}</Label>
              <Input
                id="password"
                v-model="password"
                type="password"
                autocomplete="new-password"
                required
                @input="clearErrorOnInput"
                :disabled="authStore.loading"
              />
            </div>

            <!-- Password Verify -->
            <div class="grid gap-2">
              <Label for="password-verify">{{ $t('auth:signup.password_verify_label') }}</Label>
              <Input
                id="password-verify"
                v-model="passwordVerify"
                type="password"
                autocomplete="new-password"
                required
                :disabled="authStore.loading"
              />
              <div v-if="passwordMatchError" data-testid="error-password-mismatch" class="text-sm text-red-600">{{ passwordMatchError }}</div>
            </div>

            <!-- Registration Error -->
            <div v-if="authStore.error" class="text-sm text-red-600 bg-red-50 border border-red-200 rounded p-3">
              <span v-if="authStore.error == 'REGISTER_USER_ALREADY_EXISTS'" data-testid="error-email-exists">
                {{ $t('auth:signup.error_user_exists') }}
              </span>
              <span v-else-if="authStore.error == 'REGISTER_INVALID_PASSWORD'" data-testid="error-invalid-password">{{ authStore.error }}</span>
              <span v-else-if="authStore.error == 'USERNAME_ALREADY_EXISTS'" data-testid="error-username-exists">{{ $t('auth:signup.error_username_taken') }}</span>
              <span v-else-if="authStore.error == 'Username contains inappropriate language'" data-testid="error-username-profanity">{{ $t('auth:signup.error_username_profanity') }}</span>
              <span v-else>{{ authStore.error }}</span>
            </div>

            <Button data-testid="btn-signup-submit" type="submit" class="w-full" :disabled="!isFormValid || authStore.loading">
              <div v-if="authStore.loading" class="flex items-center gap-2">
                <div class="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin"></div>
                {{ $t('auth:signup.creating_account') }}
              </div>
              <span v-else>{{ $t('auth:signup.create_account') }}</span>
            </Button>
            <Button data-testid="btn-google-signup" variant="outline" class="w-full" @click="authStore.social_login('google')" :disabled="authStore.loading">
              <svg class="w-4 h-4 mr-2" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
              </svg>
              {{ $t('auth:signup.google_signup') }}
            </Button>
          </div>
        </form>

        <div class="mt-4 text-center text-sm">
          {{ $t('auth:signup.have_account') }}
          <button @click="handle_signin_click" class="underline text-primary hover:text-primary/80"> {{ $t('ui:action.signin') }} </button>
        </div>
      </CardContent>
    </Card>
  </div>
</template>
