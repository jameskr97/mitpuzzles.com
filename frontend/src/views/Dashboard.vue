<script setup lang="ts">
import Container from "@/core/components/ui/Container.vue";
import GraphPlayedHeatmap from "@/features/graphs/components/GraphPlayedHeatmap.vue";
import TimelinePuzzleSubmissions from "@/features/graphs/components/TimelinePuzzleSubmissions.vue";
import GraphConfigurableScatter from "@/features/graphs/components/GraphConfigurableScatter.vue";
import GraphConfigurableHistogram from "@/features/graphs/components/GraphConfigurableHistogram.vue";
</script>

<template>
  <div class="grid grid-cols-4 gap-2">
    <!-- header -->
    <Container class="text-center text-2xl col-span-4">work-in-progress dashboard</Container>

    <!-- puzzle submissions -->
    <TimelinePuzzleSubmissions :num_games="8" class="col-span-4" />
    <GraphConfigurableHistogram class="col-span-2" />
    <GraphConfigurableScatter class="col-span-2" />

    <!-- played puzzles -->
    <GraphPlayedHeatmap class="col-span-4" :cell-size="10" :hide-unplayed="true" />
<!--    <GraphClassMetrics class="col-span-2" />-->
  </div>
</template>

<style scoped></style>
