<script setup lang="ts">
import AppSidebar from "@/components/AppSidebar.vue";
import { useRoute } from "vue-router";
import { SidebarProvider } from "@/components/ui/sidebar";
import AppMobileNavbar from "@/components/AppMobileNavbar.vue";
import { TooltipProvider } from "@/components/ui/tooltip";
import { useAppConfig } from "@/store/app.ts";

const route = useRoute();
const app = useAppConfig();
</script>

<template>
  <Suspense>
    <TooltipProvider>
      <SidebarProvider>
        <AppSidebar v-if="app.isFreeplay" />
        <main class="h-full w-full box-content">
          <AppMobileNavbar v-if="app.isFreeplay" />
          <router-view v-slot="{ Component, route }">
            <component :is="Component" :key="route.path" />
          </router-view>
        </main>
      </SidebarProvider>
    </TooltipProvider>

    <!--        <div class="h-dvh">-->
    <!--          <div v-if="isExperiment" class="h-dvh">-->
    <!--             <div class="flex flex-col h-dvh">-->
    <!--                <router-view v-slot="{ Component }">-->
    <!--                  <component :is="Component" :key="$route.path" />-->
    <!--                </router-view>-->
    <!--              </div>-->
    <!--          </div>-->

    <!--          <div v-else class="drawer sm:drawer-open">-->
    <!--            <input type="checkbox" class="drawer-toggle" />-->

    <!--            &lt;!&ndash; The "drawer-side" is the sidebar element &ndash;&gt;-->
    <!--            <Sidebar class="drawer-side" />-->

    <!--            &lt;!&ndash; The drawer-content, is the bigger side of the page.  &ndash;&gt;-->
    <!--                <div class="drawer-content flex flex-col h-full">-->
    <!--                  <div class="p-2 h-full">-->
    <!--                    <router-view v-slot="{ Component }">-->
    <!--                      <component :is="Component" :key="$route.path" />-->
    <!--                    </router-view>-->
    <!--                  </div>-->
    <!--                  <ConsentPopup v-if="!visitor.accepted_cookies" />-->
    <!--                </div>-->
    <!--              </div>-->
    <!--            </div>-->
  </Suspense>
</template>
