<script setup lang="ts">
import AppSidebar from "@/components/AppSidebar.vue";
import { SidebarProvider } from "@/components/ui/sidebar";
import AppMobileNavbar from "@/components/AppMobileNavbar.vue";
import { TooltipProvider } from "@/components/ui/tooltip";
import UserUsernameModal from "@/components/UserUsernameModal.vue";
import { useAuthStore } from "@/store/useAuthStore";
import { useRoute } from "vue-router";
import { computed } from "vue";

const authStore = useAuthStore();
const route = useRoute();

const showUsernameModal = computed(() => authStore.needsUsername);

// computed property to handle sidebar visibility logic
const shouldShowSidebar = computed(() => {
  const showSidebarMeta = route.meta.showSidebar;
  if (typeof showSidebarMeta === 'function') return showSidebarMeta();
  return showSidebarMeta !== false;
});

</script>

<template>
  <Suspense>
    <TooltipProvider>
      <SidebarProvider>
        <AppSidebar v-if="shouldShowSidebar" />
        <main class="h-[100dvh] w-full box-content">
          <AppMobileNavbar v-if="shouldShowSidebar" />
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

<style>
/* override reka-ui's excessive body padding when dropdowns open */
body[style*="padding-right"] {
  padding-right: 0 !important;
}
</style>
