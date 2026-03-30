<script setup lang="ts">
import { Button } from "@/core/components/ui/button";
import Container from "@/core/components/ui/Container.vue";
import { useAppStore } from "@/core/store/useAppStore.ts";

const appStore = useAppStore();
</script>

<template>
  <Container
    class="w-full justify-center text-lg font-semibold text-gray-700 flex flex-col md:flex-row mx-auto items-center"
  >
    <span>{{ $t("home:track_progress_prompt") }}</span>
    <div class="flex gap-2 ml-2">
      <Button @click="appStore.open_login_modal()">
        {{ $t("home:login_action") }}
      </Button>
      <router-link :to="{ name: 'signup' }">
        <Button>
          {{ $t("home:signup_action") }}
        </Button>
      </router-link>
    </div>
  </Container>
</template>

<style scoped></style>
