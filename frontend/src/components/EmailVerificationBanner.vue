<script setup lang="ts">
import { computed, ref } from "vue";
import { useAuthStore } from "@/store/useAuthStore";
import { useRoute } from "vue-router";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";

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

  try {
    await authStore.resend_verification_email();
    resendSuccess.value = true;
    setTimeout(() => {
      resendSuccess.value = false;
    }, 5000);
  } catch (error: any) {
    if (error.response?.status === 429) {
      resendError.value = "Please wait before requesting another verification email.";
    } else {
      resendError.value = "Failed to send verification email. Please try again.";
    }
    setTimeout(() => {
      resendError.value = "";
    }, 5000);
  } finally {
    isResending.value = false;
  }
};
</script>

<template>
  <Alert v-if="should_show_banner" variant="warning" class="mb-0">
    <AlertDescription class="flex items-center justify-between">
      <span>Please check your inbox and verify your email.</span>
      <div class="flex items-center gap-2">
        <span v-if="resendSuccess" class="text-green-700 text-sm">Verification email sent!</span>
        <span v-if="resendError" class="text-red-700 font-bold text-sm">{{ resendError }}</span>
        <Button variant="outline" size="sm"
          :disabled="isResending || resendSuccess"
          @click="resend_verification_email"
          class="bg-white"
        >
          <div v-if="isResending" class="flex items-center gap-2">
            <div class="w-3 h-3 border-2 border-current border-t-transparent rounded-full animate-spin"></div>
            Sending...
          </div>
          <span v-else>Resend Verification Email</span>
        </Button>
      </div>
    </AlertDescription>
  </Alert>
</template>
