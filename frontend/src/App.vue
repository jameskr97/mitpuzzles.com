<script setup lang="ts">
import Sidebar from "@/components/sidebar/sidebar.vue";
</script>

<template>
  <Suspense>
    <div class="drawer sm:drawer-open">
      <input type="checkbox" class="drawer-toggle" />

      <!-- The "drawer-side" is the sidebar element -->
      <Sidebar class="drawer-side" />

      <!-- The drawer-content, is the bigger side of the page.  -->
      <div class="drawer-content flex flex-col">
        <div class="p-2 h-full">
          <router-view v-slot="{ Component }">
            <component :is="Component" :key="$route.path" />
          </router-view>
        </div>
      </div>
    </div>
  </Suspense>
</template>
