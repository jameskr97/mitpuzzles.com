<script setup lang="ts">
import SidebarUserAnon from "@/components/sidebar/sidebar.user.anon.vue";
import SidebarUserAuth from "@/components/sidebar/sidebar.user.auth.vue";
import { useAuthStore } from "@/store/auth";
import { ACTIVE_GAMES } from "@/main";

const auth = useAuthStore();
auth.updateStore();
</script>

<template>
  <div class="flex flex-row max-w-60 p-0">
    <div class="menu bg-base-200 text-base-content min-h-full p-0">
      <!-- Sidebar Header -->
      <router-link to="/">
        <li class="text-lg mx-auto mt-2 sticky top-0 text-center">mitpuzzles.com</li>
      </router-link>
      <div class="divider m-0"></div>
      <div class="p-2">
        <router-link v-for="game in ACTIVE_GAMES" :key="game.key" :to="{ name: 'game-' + game.key }">
          <li class="m-0">
            <a href="#">
              {{ game.name }}
            </a>
          </li>
        </router-link>
      </div>
      <!-- Hide sidebar for now. -->
      <!-- Sidebar Footer -->
      <div class="mt-auto border-t-2 h-19 border-red-60 sticky bottom-0 bg-base-200 w-full">
        <SidebarUserAnon v-if="!auth.isAuthenticated" class="p-4" />
        <SidebarUserAuth v-else class="p-2" />
      </div>
    </div>
  </div>
</template>
