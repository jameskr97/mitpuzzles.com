<script setup lang="ts">
import AppLogo from "@/components/AppLogo.vue";
import Container from "@/components/ui/Container.vue";
import { Alert } from "@/components/ui/alert";

const props = defineProps<{ reason?: string | null; }>();
</script>

<template>
  <div class="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
    <div class="m-10">

    <div class="sm:mx-auto sm:w-full sm:max-w-md">
      <AppLogo />
    </div>

    <Container class="mt-5 sm:mx-auto sm:w-full sm:max-w-md text-center p-4">
      <h2 class="text-2xl font-bold text-gray-900 mb-4">mitpuzzles.com under maintenance.</h2>

      <Alert v-if="props.reason" variant="info" class="my-2">
          <div>{{ props.reason }}</div>
      </Alert>
      <p class="text-gray-600 mb-6">Please check back shortly. Thank you for your patience.</p>
    </Container>
  </div>
    </div>

</template>
