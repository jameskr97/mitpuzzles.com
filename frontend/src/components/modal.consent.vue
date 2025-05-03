<script setup lang="ts">
import { useVisitorStore } from "@/store/visitor.ts";
const visitor = useVisitorStore();
</script>
<template>
  <div class="toast toast-end">
    <div class="card w-96 bg-base-100 card-md shadow-sm">
      <div class="card-body">
        <h2 class="card-title">We use cookies</h2>
        <p>
          <span
            >This website uses cookies to help with our research, and to improve your experience on this website.</span
          >
          <router-link :to="{ name: 'about-us' }" class="link text-blue-500">Click here</router-link>
          <span>for more information about the information we collect.</span>
        </p>
        <div class="card-actions">
          <button @click="visitor.setCookieConsent(true)" class="btn btn-primary w-full">Okay</button>
        </div>
      </div>
    </div>
  </div>
</template>
