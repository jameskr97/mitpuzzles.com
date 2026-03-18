<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useAuthStore } from "@/core/store/useAuthStore.ts";
import { Card, CardDescription, CardHeader, CardTitle } from "@/core/components/ui/card";
import posthog from "posthog-js";
import { useTranslation } from "i18next-vue";

const { t } = useTranslation();
const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();
const errorMessage = ref("");

onMounted(async () => {
  const token = route.query.token as string;
  if (!token) {
    errorMessage.value = t("auth:verification.error_no_token");
    return;
  }

  const success = await authStore.verifyEmail(token);

  if (success) {
    posthog.capture('email_verified', {
      user_id: authStore.user?.id,
      email: authStore.user?.email,
    });
    await authStore.fetchCurrentUser();
    await router.push("/?verified=true");
  } else if (authStore.error === "VERIFY_USER_ALREADY_VERIFIED") {
    await router.push("/?alreadyVerified=true");
  } else if (authStore.error === "VERIFY_USER_BAD_TOKEN") {
    errorMessage.value = t("auth:verification.error_bad_token");
  } else {
    errorMessage.value = t("auth:verification.error_generic");
  }
});
</script>

<template>
  <div class="flex h-full w-full items-center justify-center p-4">
    <Card class="mx-auto md:w-[400px] w-full">
      <CardHeader class="text-center">
        <CardTitle class="text-xl">
          {{ errorMessage ? $t('auth:verification.failed_title') : $t('auth:verification.verifying_title') }}
        </CardTitle>
        <CardDescription>
          <div v-if="!errorMessage" class="flex flex-col items-center">
            <div class="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
          </div>
          <div v-else class="text-center space-y-2">
            <p data-testid="error-verification" class="text-red-600">{{ errorMessage }}</p>
            <a href="/signup" class="text-primary underline">{{ $t('auth:verification.back_to_signup') }}</a>
          </div>
        </CardDescription>
      </CardHeader>
    </Card>
  </div>
</template>
