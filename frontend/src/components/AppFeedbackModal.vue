<script setup lang="ts">
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { submitFeedback } from "@/services/app.ts";
import logger from "@/services/logger.ts";
import { ref } from "vue";

interface Metadata {
  url: string;
  puzzle_id?: number;
}

// References
const submitted = ref(false);
const submitting = ref(false);
const feedback = ref("");

async function submit() {
  const metadata: Metadata = { url: window.location.pathname };

  submitting.value = true;
  try {
    const res = await submitFeedback(feedback.value, metadata);
    if (res.status !== 201) logger.error("Failed to submit feedback", res);

    feedback.value = "";
    submitted.value = true;
    setTimeout(() => (submitted.value = false), 3000);
    logger.info("Feedback submitted successfully");
  } catch (e: any) {
    logger.error("Failed to submit feedback", e);
  } finally {
    submitting.value = false;
  }
}
</script>

<template>
  <Dialog>
    <DialogTrigger>
      <slot></slot>
    </DialogTrigger>
    <DialogContent>
      <DialogHeader>
        <DialogTitle>Send us your feedback!</DialogTitle>
        <DialogDescription>
          Thanks for trying our website. Did you like it? Did something not work right! Let us know here!
        </DialogDescription>
      </DialogHeader>

      <Textarea
        v-model="feedback"
        class="h-40 placeholder:italic resize-none shadow"
        placeholder="Share your thoughts here!"
      ></Textarea>

      <DialogFooter>
        <Button @click.prevent="submit"> Submit </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>
