<script setup lang="ts">
import { Menubar } from "@/components/ui/menubar";
import { useSidebar } from "@/components/ui/sidebar";
import AppThemeButton from "@/components/AppThemeButton.vue";
import AppLogo from "@/components/AppLogo.vue";

const sidebar = useSidebar();
</script>

<template>
  <Menubar v-if="sidebar.isMobile.value" class="w-full h-fit flex justify-between">
    <v-icon name="bi-layout-sidebar-inset" :scale="2" @click="sidebar.toggleSidebar" />
    <AppLogo img-class="h-10" />
    <!--    <img src="/assets/logo.light.png" alt="mitpuzzles.com logo" class="h-10" />-->
    <AppThemeButton />
  </Menubar>
</template>
