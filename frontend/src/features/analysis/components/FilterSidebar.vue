<script setup lang="ts">
import Container from "@/core/components/ui/Container.vue"
import { Button } from "@/core/components/ui/button"
import FilterSidebarBrowser from "@/features/analysis/components/FilterSidebarBrowser.vue"
import FilterSidebarDownload from "@/features/analysis/components/FilterSidebarDownload.vue"
import { useAnalysisStore } from '@/features/analysis/stores/useAnalysisStore'

defineProps<{
  activeTab: string
}>()

const store = useAnalysisStore()
</script>

<template>
  <Container class="w-64 min-w-[200px] flex flex-col overflow-hidden">
    <h2 class="text-lg font-semibold text-center mb-4 shrink-0">Filters</h2>

    <div class="flex-1 overflow-y-auto">

    <!-- Analytics-specific filters -->
    <template v-if="activeTab === 'analytics'">
      <div class="text-sm text-gray-500 text-center">
        Analytics filters (coming soon)
      </div>
    </template>

    <!-- Download/SQL-specific filters -->
    <FilterSidebarDownload v-else-if="activeTab === 'download' || activeTab === 'sql'" />

    <!-- Browser-specific filters -->
    <FilterSidebarBrowser v-else-if="activeTab === 'browser'" />
    </div>

    <!-- Clear Filters Button -->
    <Button variant="secondary" class="mt-4 w-full shrink-0" @click="store.clear_all">
      Clear All Filters
    </Button>
  </Container>
</template>

