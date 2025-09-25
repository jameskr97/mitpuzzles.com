<script setup lang="ts">
import AppSidebar from "@/components/AppSidebar.vue";
import { SidebarProvider } from "@/components/ui/sidebar";
import AppMobileNavbar from "@/components/AppMobileNavbar.vue";
import { TooltipProvider } from "@/components/ui/tooltip";
import UserUsernameModal from "@/components/UserUsernameModal.vue";
import { useAppStore } from "@/store/useAppStore.ts";
import { useAuthStore } from "@/store/useAuthStore";
import { computed } from "vue";

const app = useAppStore();
const authStore = useAuthStore();

const showUsernameModal = computed(() => authStore.needsUsername);

</script>

<template>
  <Suspense>
    <TooltipProvider>
      <SidebarProvider>
        <AppSidebar v-if="$route.meta.showSidebar !== false" />
        <main class="h-[100dvh] w-full box-content">
          <AppMobileNavbar v-if="$route.meta.showSidebar !== false" />
          <router-view v-slot="{ Component, route }">
            <component :is="Component" :key="route.path" />
          </router-view>
        </main>
      </SidebarProvider>

      <!-- show username mode if the user doesn't have a username -->
      <UserUsernameModal :show="showUsernameModal" />
    </TooltipProvider>
  </Suspense>
</template>
