<script setup lang="ts">
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { computed, ref, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import AppLogo from "@/components/AppLogo.vue";
import axios from "axios";
import { useTranslation } from "i18next-vue";
import { useAppStore } from "@/store/useAppStore.ts";

const { t } = useTranslation();

const route = useRoute();
const router = useRouter();
const appStore = useAppStore();

const token = ref("");
const new_password = ref("");
const confirm_password = ref("");
const loading = ref(false);
const error = ref("");
const success = ref(false);

const password_match_error = computed(() => {
  if (!new_password.value || !confirm_password.value) return "";
  return new_password.value === confirm_password.value ? "" : t("ui:validation.password_mismatch");
});

const is_form_valid = computed(() => {
  return new_password.value && confirm_password.value && !password_match_error.value;
});

const clear_error_on_input = () => {
  if (error.value) {
    error.value = "";
  }
};

const submit_form = async () => {
  loading.value = true;
  error.value = "";
  success.value = false;

  try {
    await axios.post("/api/auth/reset-password", {
      token: token.value,
      password: new_password.value,
    });
    success.value = true;

    // Redirect to login after 3 seconds
    setTimeout(() => {
      appStore.open_login_modal();
      router.push("/");
    }, 3000);
  } catch (err: any) {
    error.value = err.response?.data?.detail || "Failed to reset password";
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  // Get token from URL query parameter
  token.value = (route.query.token as string) || "";

  if (!token.value) {
    error.value = t("auth:reset_password.error_invalid_token");
  }
});
</script>

<template>
  <div class="flex flex-col h-full w-full items-center justify-center p-4">
    <Card class="mx-auto md:w-[400px] w-full">
      <CardHeader class="text-center">
        <AppLogo class="w-80 mb-4 mx-auto" />
        <Separator />
        <CardTitle class="text-2xl">{{ $t('auth:reset_password.title') }}</CardTitle>
        <CardDescription>{{ $t('auth:reset_password.description') }}</CardDescription>
      </CardHeader>
      <CardContent>
        <div v-if="!success">
          <form @submit.prevent="submit_form">
            <div class="grid gap-4">
              <!-- New Password -->
              <div class="grid gap-2">
                <Label for="new-password">{{ $t('account:password.new') }}</Label>
                <Input
                  id="new-password"
                  v-model="new_password"
                  type="password"
                  autocomplete="new-password"
                  required
                  @input="clear_error_on_input"
                  :disabled="loading || !token"
                />
              </div>

              <!-- Confirm Password -->
              <div class="grid gap-2">
                <Label for="confirm-password">{{ $t('auth:reset_password.confirm_password') }}</Label>
                <Input
                  id="confirm-password"
                  v-model="confirm_password"
                  type="password"
                  autocomplete="new-password"
                  required
                  :disabled="loading || !token"
                />
                <div v-if="password_match_error" class="text-sm text-red-600">
                  {{ password_match_error }}
                </div>
              </div>

              <!-- Error Message -->
              <div v-if="error && error === 'RESET_PASSWORD_BAD_TOKEN'" data-testid="error-bad-token" class="text-sm text-red-600 bg-red-50 border border-red-200 rounded p-3">
                {{ $t('auth:reset_password.error_invalid_token') }}
              </div>

              <Button data-testid="btn-reset-password-submit" type="submit" class="w-full" :disabled="!is_form_valid || loading || !token">
                <div v-if="loading" class="flex items-center gap-2">
                  <div class="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin"></div>
                  {{ $t('auth:reset_password.resetting') }}
                </div>
                <span v-else>{{ $t('auth:reset_password.reset_button') }}</span>
              </Button>
            </div>
          </form>
        </div>

        <!-- Success Message -->
        <div v-else class="text-center space-y-4">
          <div data-testid="reset-password-success" class="text-sm text-green-600 bg-green-50 border border-green-200 rounded p-4">
            <p class="font-semibold mb-2">{{ $t('auth:reset_password.success_title') }}</p>
            <p>{{ $t('auth:reset_password.success_message') }}</p>
            <p class="mt-2">{{ $t('auth:reset_password.redirecting') }}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  </div>
</template>
