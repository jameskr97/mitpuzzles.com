<script setup lang="ts">
import { useAuthStore } from "@/store/auth";
const auth = useAuthStore();
</script>

<template>
  <div class="flex flex-row gap-2">
    <div class="skeleton h-14 w-10"></div>
    <div class="flex flex-col">
      <p>{{ auth.user?.display }}</p>
      <button class="btn btn-error btn-xs" @click="auth.logout()">Log out</button>
    </div>
  </div>
</template>
