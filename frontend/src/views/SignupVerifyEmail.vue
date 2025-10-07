<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useAuthStore } from "@/store/useAuthStore.ts";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import posthog from "posthog-js";

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();
const errorMessage = ref("");

onMounted(async () => {
  const token = route.query.token as string;
  if (!token) {
    errorMessage.value = "No verification token provided.";
    return;
  }

  try {
    await authStore.verifyEmail(token);
    // track email verification with posthog
    posthog.capture('email_verified', {
      user_id: authStore.user?.id,
      email: authStore.user?.email
    });

    // fetch current user to update verification status and auto-login
    await authStore.fetchCurrentUser();
    await router.push("/?verified=true");
  } catch (error: any) {
    console.log("Verification error:", error);

    // handle different error cases based on status and detail
    if (error.response?.status === 400) {
      const errorDetail = error.response?.data?.detail;

      if (errorDetail === "VERIFY_USER_ALREADY_VERIFIED") {
        // User already verified - redirect to home
        await router.push("/?alreadyVerified=true");
      } else if (errorDetail === "VERIFY_USER_BAD_TOKEN") {
        // Bad token - shouldn't happen, but show support message
        errorMessage.value = "Invalid verification token. Please contact support@mitpuzzles.com for assistance.";
      } else {
        // Other 400 errors
        errorMessage.value = "Verification failed. Please contact support@mitpuzzles.com for assistance.";
      }
    } else if (error.response?.status === 422) {
      // Validation error - shouldn't happen in normal flow
      errorMessage.value = "An unexpected error occurred. Please contact support@mitpuzzles.com if this persists.";
    } else {
      // Generic error fallback
      errorMessage.value = error.message || "Verification failed. Please try again or contact support@mitpuzzles.com.";
    }
  }
});
</script>

<template>
  <div class="flex h-full w-full items-center justify-center p-4">
    <Card class="mx-auto md:w-[400px] w-full">
      <CardHeader class="text-center">
        <CardTitle class="text-xl">
          {{ errorMessage ? "Verification Failed" : "Verifying Your Email" }}
        </CardTitle>
        <CardDescription>
          <div v-if="!errorMessage" class="flex flex-col items-center">
            <div class="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
          </div>
          <div v-else class="text-center space-y-2">
            <p class="text-red-600">{{ errorMessage }}</p>
            <a href="/signup" class="text-primary underline">Back to Sign Up</a>
          </div>
        </CardDescription>
      </CardHeader>
    </Card>
  </div>
</template>
