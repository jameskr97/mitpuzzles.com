<script setup lang="ts">
import { ref } from "vue";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/core/components/ui/tabs";
import UploadTab from "@/features/puzzle-manager/tabs/UploadTab.vue";
import PuzzleAuditTab from "@/features/puzzle-manager/tabs/PuzzleAuditTab.vue";

const active_tab = ref("upload");
</script>

<template>
  <Tabs v-model="active_tab" class="w-full h-full flex flex-col">
    <div class="flex flex-col gap-2 h-full p-4">
      <div class="flex flex-col gap-1 w-full">
        <TabsList class="w-full md:w-auto">
          <TabsTrigger value="upload">Upload</TabsTrigger>
          <TabsTrigger value="audit">Puzzle Audit</TabsTrigger>
        </TabsList>
      </div>

      <TabsContent value="upload" class="h-full">
        <UploadTab />
      </TabsContent>

      <TabsContent value="audit" class="h-full">
        <PuzzleAuditTab />
      </TabsContent>
    </div>
  </Tabs>
</template>
