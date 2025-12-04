<script setup lang="ts">
import { Menubar } from "@/core/components/ui/menubar";
import { useSidebar } from "@/core/components/ui/sidebar";
import AppThemeButton from "@/core/components/AppThemeButton.vue";
import AppLogo from "@/core/components/AppLogo.vue";

const sidebar = useSidebar();
</script>

<template>
  <Menubar v-if="sidebar.isMobile.value" class="w-full h-fit flex justify-between">
    <v-icon data-testid="btn-mobile-menu" name="bi-layout-sidebar-inset" :scale="2" @click="sidebar.toggleSidebar" />
    <AppLogo img-class="h-10" />
    <!--    <img src="/assets/logo.light.png" alt="mitpuzzles.com logo" class="h-10" />-->
    <AppThemeButton />
  </Menubar>
</template>
