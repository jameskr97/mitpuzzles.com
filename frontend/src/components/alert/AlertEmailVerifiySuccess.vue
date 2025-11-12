<script setup lang="ts">
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
</script>

<template>
  <Alert class="mt-2 bg-green-50 border-green-200">
    <svg
      xmlns="http://www.w3.org/2000/svg"
      class="h-5 w-5 text-green-600"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
    >
      <path
        stroke-linecap="round"
        stroke-linejoin="round"
        stroke-width="2"
        d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
      />
    </svg>
    <AlertTitle class="text-green-800">{{ $t('auth:verification.success_title') }}</AlertTitle>
    <AlertDescription class="text-green-700">
      {{ $t('auth:verification.success_message') }}
    </AlertDescription>
  </Alert>
</template>
