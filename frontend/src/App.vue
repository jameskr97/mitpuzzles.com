<script setup lang="ts">
import Sidebar from "@/components/ui/sidebar/sidebar.vue";
import Footer from "@/components/ui/base/footer.vue";
</script>

<template>
  <Suspense>
    <div class="drawer drawer-open">
      <input type="checkbox" class="drawer-toggle" />

      <!-- The "drawer-side" is the sidebar element -->
      <Sidebar class="drawer-side" />

      <!-- The drawer-content, is the bigger side of the page.  -->
      <div class="drawer-content flex flex-col">
        <div class="p-2">
          <router-view v-slot="{ Component }">
            <component :is="Component" :key="$route.path" />
          </router-view>
        </div>
        <Footer class="mt-auto" />
      </div>
    </div>
  </Suspense>
</template>
