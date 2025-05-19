<script setup lang="ts">
// import SidebarUserAnon from "@/components/sidebar/sidebar.user.anon.vue";
// import SidebarUserAuth from "@/components/sidebar/sidebar.user.auth.vue";
import { ACTIVE_GAMES, DEV_TOOLS } from "@/main";
import FloatingFeedback from "@/components/button.feedback.vue";
import { useAuthStore } from "@/store/auth.ts";

const isDev = import.meta.env.DEV;
const user = useAuthStore();
</script>

<template>
  <div class="flex flex-row min-w-60 p-0">
    <div class="menu text-base-content min-h-full w-full p-0 bg-platinum">
      <!-- Sidebar Header -->
      <router-link to="/">
        <li class="text-lg mx-auto mt-2 sticky top-0 text-center underline">mitpuzzles.com</li>
      </router-link>

      <!--      <div class="divider m-0"></div>-->
      <div class="p-2">
        <router-link v-for="game in Object.values(ACTIVE_GAMES)" :key="game.key" :to="{ name: 'game-' + game.key }">
          <li class="m-0 text-xl">
            <a href="#">
              {{ game.name }}
            </a>
          </li>
        </router-link>
      </div>

      <div v-if="isDev">
        <p class="text-lg mx-auto mt-2 sticky top-0 text-center underline">Dev Tools</p>
        <div class="p-2">
          <router-link v-for="tool in DEV_TOOLS" :to="{ name: `dev-` + tool.key }">
            <li v-if="user.isAdmin || !tool.requires_admin" class="m-0 text-lg">
              <a href="#">{{ tool.name }}</a>
            </li>
          </router-link>
        </div>
      </div>

      <div class="w-full mt-auto p-2">
        <router-link :to="{ name: 'about-us' }">
          <button class="btn btn-info w-full mb-2">About Us</button>
        </router-link>
        <FloatingFeedback />
      </div>
      <!-- Hide sidebar for now. -->
      <!-- Sidebar Footer -->
      <!--      <div class="mt-auto border-t-2 h-19 border-red-60 sticky bottom-0 bg-base-200 w-full">-->
      <!--        <SidebarUserAnon v-if="!auth.isAuthenticated" class="p-4" />-->
      <!--        <SidebarUserAuth v-else class="p-2" />-->
      <!--      </div>-->
    </div>
  </div>
</template>
