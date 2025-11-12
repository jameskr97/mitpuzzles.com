<script setup lang="ts">
import { ref } from "vue";
import { storeToRefs } from "pinia";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import Container from "@/components/ui/Container.vue";
import FilterSidebar from "@/features/analysis/components/FilterSidebar.vue";
import BrowserTab from "@/features/analysis/tabs/BrowserTab.vue";
import DownloadTab from "@/features/analysis/tabs/DownloadTab.vue";
import EntitySelector from "@/features/analysis/components/EntitySelector.vue";
import { useAnalysisStore } from "@/features/analysis/stores/useAnalysisStore";

const store = useAnalysisStore();
const { selected_entity_id, scope } = storeToRefs(store);
const active_main_tab = ref("download");

</script>

<template>
  <Tabs v-model="active_main_tab" class="w-full h-full flex flex-col">
    <div class="grid grid-cols-1 md:grid-cols-[auto_1fr] grid-rows-[auto_1fr] gap-2 h-full">
      <FilterSidebar :active-tab="active_main_tab" class="hidden md:block row-span-full" />

      <div class="flex flex-col gap-1 w-full">
        <TabsList class="w-full md:w-auto">
          <TabsTrigger value="download">Download</TabsTrigger>
          <TabsTrigger value="browser">Browser</TabsTrigger>
        </TabsList>

        <!-- Tab Set 2: Scope (hidden for browser tab) -->
        <div v-if="active_main_tab !== 'browser'">
          <Tabs v-model="scope" class="w-full">
            <div class="flex flex-col md:flex-row md:items-center gap-2">
              <TabsList class="w-full">
                <TabsTrigger value="device">By Device</TabsTrigger>
                <TabsTrigger value="user">By User</TabsTrigger>
              </TabsList>

              <!-- Entity Picker -->
              <EntitySelector v-model="selected_entity_id" :scope="scope" />
            </div>
          </Tabs>
        </div>
      </div>

      <!-- Main Tab Content -->
      <TabsContent value="download" class="h-full">
        <DownloadTab />
      </TabsContent>

      <TabsContent value="browser">
        <BrowserTab class="h-full" />
      </TabsContent>
    </div>
  </Tabs>

  <!--  <div class="flex flex-col md:flex-row h-full">-->

  <!--    &lt;!&ndash; Main Content Area &ndash;&gt;-->
  <!--    <div class="flex-1 flex flex-col m-2 overflow-hidden h-full">-->
  <!--      &lt;!&ndash; Tab Set 1: Main Interface &ndash;&gt;-->

  <!--    </div>-->
  <!--  </div>-->
</template>

<style scoped></style>
