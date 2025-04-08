<script setup lang="ts">
import { useAuthStore } from "@/store/auth";
const auth = useAuthStore();
</script>

<template>
  <div class="flex flex-row justify-between gap-2 align-middle h-full">
    <p class="text-3xl">{{ auth.user?.display }}</p>
    <button class="btn btn-error btn-xs w-15 h-14" @click="auth.logout()">Log out</button>
  </div>
</template>
