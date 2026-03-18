<script setup lang="ts">
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/core/components/ui/dialog";
import { Textarea } from "@/core/components/ui/textarea";
import { Button } from "@/core/components/ui/button";
import { api } from "@/core/services/client";
import { capture_error } from "@/core/services/posthog.ts";
import { ref } from "vue";
import { useAuthStore } from "@/core/store/useAuthStore.ts";

interface Metadata {
  url: string;
  puzzle_id?: number;
  user?: any;
  [key: string]: unknown;
}

const submitted = ref(false);
const submitting = ref(false);
const feedback = ref("");
const user = useAuthStore();

async function submit() {
  const metadata: Metadata = { url: window.location.pathname };
  if (user.isAuthenticated) metadata.user = user.user;

  submitting.value = true;
  const { error } = await api.POST("/api/feedback", {
    body: { message: feedback.value, feedback_metadata: metadata } as any,
  });
  submitting.value = false;

  if (error) {
    capture_error("feedback_submit_failed", error);
    return;
  }

  feedback.value = "";
  submitted.value = true;
  setTimeout(() => (submitted.value = false), 3000);
}
</script>

<template>
  <Dialog>
    <DialogTrigger>
      <slot></slot>
    </DialogTrigger>
    <DialogContent>
      <DialogHeader>
        <DialogTitle>{{ $t('ui:feedback.title') }}</DialogTitle>
        <DialogDescription class="text-md">
          {{ $t('ui:feedback.description') }}
        </DialogDescription>
      </DialogHeader>

      <Textarea
        v-model="feedback"
        class="h-40 placeholder:italic resize-none shadow"
        :placeholder="$t('ui:feedback.placeholder')"
      ></Textarea>

      <DialogFooter>
        <Button @click.prevent="submit">{{ $t('ui:action.submit') }}</Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>
