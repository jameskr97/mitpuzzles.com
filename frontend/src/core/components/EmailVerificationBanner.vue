<script setup lang="ts">
import { computed, ref } from "vue";
import { useAuthStore } from "@/core/store/useAuthStore.ts";
import { useRoute } from "vue-router";
import { Alert, AlertDescription } from "@/core/components/ui/alert";
import { Button } from "@/core/components/ui/button";
import { useTranslation } from "i18next-vue";

const { t } = useTranslation();

const authStore = useAuthStore();
const route = useRoute();
const isResending = ref(false);
const resendSuccess = ref(false);
const resendError = ref("");

const should_show_banner = computed(() => {
  const is_homepage = route.name === "Home";
  return is_homepage && authStore.isAuthenticated && authStore.user && !authStore.user.is_verified;
});

const resend_verification_email = async () => {
  if (isResending.value) return;

  isResending.value = true;
  resendError.value = "";
  resendSuccess.value = false;

  const success = await authStore.resend_verification_email();

  if (success) {
    resendSuccess.value = true;
    setTimeout(() => { resendSuccess.value = false; }, 5000);
  } else {
    resendError.value = authStore.error || t("auth:verification.error_failed");
    setTimeout(() => { resendError.value = ""; }, 5000);
  }
  isResending.value = false;
};
</script>

<template>
  <Alert v-if="should_show_banner" variant="warning" class="mb-0">
    <AlertDescription class="flex items-center justify-between">
      <span>{{ $t('auth:verification.check_inbox') }}</span>
      <div class="flex items-center gap-2">
        <span v-if="resendSuccess" class="text-green-700 text-sm">{{ $t('auth:verification.sent_success') }}</span>
        <span v-if="resendError" class="text-red-700 font-bold text-sm">{{ resendError }}</span>
        <Button variant="outline" size="sm"
          :disabled="isResending || resendSuccess"
          @click="resend_verification_email"
          class="bg-white"
        >
          <div v-if="isResending" class="flex items-center gap-2">
            <div class="w-3 h-3 border-2 border-current border-t-transparent rounded-full animate-spin"></div>
            {{ $t('ui:action.sending') }}
          </div>
          <span v-else>{{ $t('auth:verification.resend') }}</span>
        </Button>
      </div>
    </AlertDescription>
  </Alert>
</template>
