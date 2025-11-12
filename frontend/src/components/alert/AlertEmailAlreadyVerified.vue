<script setup lang="ts">
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
</script>

<template>
  <Alert class="mt-2 bg-blue-50 border-blue-200">
    <svg
      xmlns="http://www.w3.org/2000/svg"
      class="h-5 w-5 text-blue-600"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
    >
      <path
        stroke-linecap="round"
        stroke-linejoin="round"
        stroke-width="2"
        d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
      />
    </svg>
    <AlertTitle class="text-blue-800">{{ $t('auth:verification.already_verified_title') }}</AlertTitle>
    <AlertDescription class="text-blue-700">
      {{ $t('auth:verification.already_verified_message') }}
    </AlertDescription>
  </Alert>
</template>
