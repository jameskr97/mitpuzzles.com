<script setup lang="ts">
import { Button } from "@/core/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/core/components/ui/dialog";
import { Input } from "@/core/components/ui/input";
import { Label } from "@/core/components/ui/label";
import { computed, ref, watch } from "vue";
import { api } from "@/core/services/client";
import { useTranslation } from "i18next-vue";

const { t } = useTranslation();

const props = defineProps<{
  open: boolean;
}>();

const emit = defineEmits<{
  (e: "update:open", value: boolean): void;
}>();

const email = ref("");
const loading = ref(false);
const error = ref("");
const success = ref(false);

const email_error = computed(() => {
  if (!email.value) return "";
  const email_regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return email_regex.test(email.value) ? "" : t("ui:validation.invalid_email");
});

const is_form_valid = computed(() => {
  return email.value && !email_error.value;
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

  const { error: err } = await api.POST("/api/auth/forgot-password", { body: { email: email.value } });
  loading.value = false;

  if (err) {
    error.value = (err as any)?.detail || "Failed to send password reset email";
  } else {
    success.value = true;
  }
};

const close_modal = () => {
  emit("update:open", false);
};

// Reset form when modal closes
watch(() => props.open, (is_open) => {
  if (!is_open) {
    email.value = "";
    error.value = "";
    success.value = false;
    loading.value = false;
  }
});
</script>

<template>
  <Dialog :open="open" @update:open="close_modal">
    <DialogContent class="sm:max-w-[425px]">
      <DialogHeader data-testid="dialog-forgot-password">
        <DialogTitle>{{ $t('auth:forgot_password.title') }}</DialogTitle>
        <DialogDescription>
          {{ $t('auth:forgot_password.description') }}
        </DialogDescription>
      </DialogHeader>

      <div v-if="!success">
        <form @submit.prevent="submit_form">
          <div class="grid gap-4">
            <!-- Email -->
            <div class="grid gap-2">
              <Label for="forgot-email">{{ $t('ui:form.email') }}</Label>
              <Input
                id="forgot-email"
                v-model="email"
                type="email"
                :placeholder="$t('ui:form.email')"
                required
                @input="clear_error_on_input"
                :disabled="loading"
              />
              <div v-if="email_error" class="text-sm text-red-600">{{ email_error }}</div>
            </div>

            <!-- Error Message -->
            <div v-if="error" class="text-sm text-red-600 bg-red-50 border border-red-200 rounded p-3">
              {{ error }}
            </div>

            <div class="flex gap-2">
              <Button type="button" variant="outline" @click="close_modal" class="flex-1" :disabled="loading">
                {{ $t('ui:action.cancel') }}
              </Button>
              <Button data-testid="btn-forgot-password-submit" type="submit" class="flex-1" :disabled="!is_form_valid || loading">
                <div v-if="loading" class="flex items-center gap-2">
                  <div class="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin"></div>
                  {{ $t('ui:action.sending') }}
                </div>
                <span v-else>{{ $t('auth:forgot_password.send_link') }}</span>
              </Button>
            </div>
          </div>
        </form>
      </div>

      <!-- Success Message -->
      <div v-else class="space-y-4">
        <div data-testid="forgot-password-success" class="text-sm text-green-600 bg-green-50 border border-green-200 rounded p-4">
          <p class="font-semibold mb-2">{{ $t('auth:forgot_password.success_title') }}</p>
          <p v-html="$t('auth:forgot_password.success_message', { email })"></p>
          <p class="mt-2">{{ $t('auth:forgot_password.link_expires') }}</p>
        </div>

        <Button @click="close_modal" class="w-full">
          {{ $t('ui:action.done') }}
        </Button>
      </div>
    </DialogContent>
  </Dialog>
</template>
