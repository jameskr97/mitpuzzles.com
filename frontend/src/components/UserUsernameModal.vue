<script setup lang="ts">
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ref, watch } from "vue";
import { useAuthStore } from "@/store/useAuthStore";

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
    error.value = "Username is required";
    return;
  }

  loading.value = true;
  error.value = "";

  try {
    await authStore.updateUsername(username.value.trim());
    emit("close");
  } catch (err: any) {
    console.log(err);
    error.value = err.response.data.detail || "Failed to update username";
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <Dialog :open="show">
    <DialogContent class="sm:max-w-[425px] [&>button]:hidden" @interact-outside.prevent>
      <DialogHeader>
        <DialogTitle>Choose Username</DialogTitle>
        <DialogDescription> Please choose a username to complete your account setup. </DialogDescription>
      </DialogHeader>

      <form @submit.prevent="onSubmit" class="space-y-4">
        <div class="space-y-2">
          <Label for="username">Username</Label>
          <Input id="username" v-model="username" type="text" placeholder="Enter your username" :disabled="loading" />
          <p v-if="error" class="text-sm text-red-500">{{ error }}</p>
          <p class="text-sm text-muted-foreground">This is your public display name.</p>
        </div>

        <DialogFooter>
          <Button type="submit" :disabled="loading || !username.trim()">
            {{ loading ? "Saving..." : "Save Username" }}
          </Button>
        </DialogFooter>
      </form>
    </DialogContent>
  </Dialog>
</template>
