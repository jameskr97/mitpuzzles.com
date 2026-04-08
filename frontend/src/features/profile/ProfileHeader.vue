<script setup lang="ts">
import Container from "@/core/components/ui/Container.vue";

defineProps<{
  username: string;
  is_own_profile: boolean;
}>();
</script>

<template>
  <Container>
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold flex items-center gap-2">
        <span class="w-2.5 h-2.5 rounded-full bg-green-500 inline-block" />
        {{ username }}
      </h1>
      <router-link
        v-if="is_own_profile"
        :to="{ name: 'account' }"
        class="text-sm text-blue-600 hover:underline"
      >
        edit profile
      </router-link>
    </div>
  </Container>
</template>
