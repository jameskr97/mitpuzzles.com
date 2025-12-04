<script setup lang="ts">
import AppSidebar from "@/core/components/AppSidebar.vue";
import { SidebarProvider } from "@/core/components/ui/sidebar";
import AppMobileNavbar from "@/core/components/AppMobileNavbar.vue";
import { TooltipProvider } from "@/core/components/ui/tooltip";
import UserUsernameModal from "@/features/auth/components/UserUsernameModal.vue";
import UserLoginModal from "@/features/auth/components/UserLoginModal.vue";
import { useAuthStore } from "@/core/store/useAuthStore";
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
        <main class="m-2 w-full box-content">
            <AppMobileNavbar v-if="shouldShowSidebar" class="mb-2" />
            <router-view v-slot="{ Component, route }">
              <component :is="Component" :key="route.path" />
            </router-view>
        </main>
      </SidebarProvider>

      <!-- Global modals -->
      <UserUsernameModal :show="showUsernameModal" />
      <UserLoginModal />
    </TooltipProvider>
  </Suspense>
</template>

<style>
/* override reka-ui's excessive body padding when dropdowns open */
body[style*="padding-right"] {
  padding-right: 0 !important;
}
</style>
