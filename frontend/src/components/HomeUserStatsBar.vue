<script setup lang="ts">
import { Separator } from "@/components/ui/separator";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import Container from "@/components/ui/Container.vue";
import { useAuthStore } from "@/store/useAuthStore.ts";
import { useAppStore } from "@/store/useAppStore.ts";
import { computed } from "vue";
import UserAvatar from "@/components/UserAvatar.vue";

const authStore = useAuthStore();
const appStore = useAppStore();

const user_stats = computed(() => [
  { label: "Total Play Time", value: "2h:30m27s" },
  { label: "Personal Best", value: '<span class="italic text-red-700">3.67s</span>' },
  { label: "Games Solved this Week", value: '<span class="italic text-red-700">19</span>' },
  { label: "Total Games Solved", value: '<span class="italic text-red-700">49</span>' },
]);
</script>

<template>
  <Container>
    <div class="relative">
      <div class="flex flex-row gap-2 h-full" :class="{ 'opacity-30 grayscale': !authStore.isAuthenticated }">
        <div class="flex flex-col class h-21 aspect-square">
          <UserAvatar :user="authStore.user" class="h-14 w-14 mx-auto rounded-lg" />
          <p v-if="authStore.isAuthenticated" class="text-xl translate-y-1 lg:mt-2 mt-auto">
            {{ authStore.user?.username }}
          </p>
          <p v-else class="text-xl translate-y-1 lg:mt-2 mt-auto">Username</p>
        </div>
        <Separator orientation="vertical" />
        <div class="grid grid-cols-[auto_1fr] gap-2 items-start leading-none auto-rows-min">
          <template v-for="stat in user_stats" :key="stat.label">
            <div class="font-bold text-right self-start text-nowrap">{{ stat.label }}</div>
            <div class="text-end" v-html="stat.value"></div>
          </template>
        </div>
      </div>

      <div
        v-if="!authStore.isAuthenticated"
        class="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 flex items-center p-2 bg-[#B8E0FF] rounded-lg mx-auto"
      >
        <p class="text-lg font-semibold text-gray-700 text-center text-nowrap">
          <span class="underline cursor-pointer hover:text-blue-600" @click="appStore.open_login_modal()"> Login </span>
          or
          <router-link class="underline cursor-pointer hover:text-blue-600" :to="{ name: 'signup' }">
            create an account
          </router-link>
          to see your stats!
        </p>
      </div>


    </div>
  </Container>
</template>

<style scoped></style>
