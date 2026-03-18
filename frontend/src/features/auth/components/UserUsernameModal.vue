<script setup lang="ts">
import { Button } from "@/core/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/core/components/ui/dialog";
import { Input } from "@/core/components/ui/input";
import { Label } from "@/core/components/ui/label";
import { ref, watch } from "vue";
import { useAuthStore } from "@/core/store/useAuthStore.ts";
import { useTranslation } from "i18next-vue";

const { t } = useTranslation();

const props = defineProps<{
  show: boolean;
}>();

const emit = defineEmits<{
  close: [];
}>();

const authStore = useAuthStore();
const username = ref("");
const loading = ref(false);
const error = ref("");

// Clear form when modal opens
watch(
  () => props.show,
  (newValue) => {
    if (newValue) {
      username.value = "";
      error.value = "";
    }
  },
);

async function onSubmit() {
  if (!username.value.trim()) {
    error.value = t("auth:username_modal.error_required");
    return;
  }

  loading.value = true;
  error.value = "";

  const result = await authStore.updateUsername(username.value.trim());
  loading.value = false;

  if (!result) {
    error.value = authStore.error || "Failed to update username";
  } else {
    emit("close");
  }
}
</script>

<template>
  <Dialog :open="show">
    <DialogContent class="sm:max-w-[425px] [&>button]:hidden" @interact-outside.prevent>
      <DialogHeader>
        <DialogTitle>{{ $t('auth:username_modal.title') }}</DialogTitle>
        <DialogDescription>{{ $t('auth:username_modal.description') }}</DialogDescription>
      </DialogHeader>

      <form @submit.prevent="onSubmit" class="space-y-4">
        <div class="space-y-2">
          <Label for="username">{{ $t('ui:form.username') }}</Label>
          <Input id="username" v-model="username" type="text" :placeholder="$t('ui:form.username')" :disabled="loading" />
          <p v-if="error" class="text-sm text-red-500">{{ error }}</p>
          <p class="text-sm text-muted-foreground">{{ $t('auth:username_modal.display_name_hint') }}</p>
        </div>

        <DialogFooter>
          <Button type="submit" :disabled="loading || !username.trim()">
            {{ loading ? $t('ui:action.saving') : $t('auth:username_modal.save_username') }}
          </Button>
        </DialogFooter>
      </form>
    </DialogContent>
  </Dialog>
</template>
