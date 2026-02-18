<script setup lang="ts">
import { Button } from "@/core/components/ui/button";
import { DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/core/components/ui/dialog";
import { DialogContent, DialogOverlay, DialogPortal, DialogRoot } from "reka-ui";
import { useAppStore } from "@/core/store/useAppStore.ts";
import { useRoute } from "vue-router";
import { computed } from "vue";

const appStore = useAppStore();
const route = useRoute();

const show = computed(() => !appStore.has_consented && route.path !== "/privacy-policy");

function leave_site() {
  window.location.href = "https://www.google.com";
}
</script>

<template>
  <DialogRoot :open="show">
    <DialogPortal>
      <DialogOverlay class="fixed inset-0 z-100 bg-black/80" />
      <DialogContent
        class="bg-background fixed top-[50%] left-[50%] z-100 grid w-full max-w-[calc(100%-2rem)] translate-x-[-50%] translate-y-[-50%] gap-4 rounded-lg border p-6 shadow-lg sm:max-w-[425px]"
        @interact-outside.prevent
      >
        <DialogHeader>
          <DialogTitle>{{ $t('ui:consent.title') }}</DialogTitle>
          <DialogDescription class="whitespace-pre-line">
            {{ $t('ui:consent.description') }}
          </DialogDescription>
        </DialogHeader>

        <a href="/privacy-policy" target="_blank" class="text-sm underline text-primary hover:text-primary/80">
          {{ $t('ui:consent.privacy_link') }}
        </a>

        <DialogFooter class="flex gap-2 sm:justify-between">
          <Button variant="outline" @click="leave_site()">
            {{ $t('ui:consent.leave') }}
          </Button>
          <Button @click="appStore.accept_consent()">
            {{ $t('ui:consent.accept') }}
          </Button>
        </DialogFooter>
      </DialogContent>
    </DialogPortal>
  </DialogRoot>
</template>
