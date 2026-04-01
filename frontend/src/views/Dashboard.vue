<script setup lang="ts">
import Container from "@/core/components/ui/Container.vue";
import GraphPlayedHeatmap from "@/features/graphs/components/GraphPlayedHeatmap.vue";
import GraphSolveTimeDistribution from "@/features/graphs/components/GraphSolveTimeDistribution.vue";
import TimelinePuzzleSubmissions from "@/features/graphs/components/TimelinePuzzleSubmissions.vue";
import GraphActionCountDistribution from "@/features/graphs/components/GraphActionCountDistribution.vue";
import GraphClassMetrics from "@/features/graphs/components/GraphClassMetrics.vue";
import GraphMistakeDistribution from "@/features/graphs/components/GraphMistakeDistribution.vue";
import GraphMinActionsDistribution from "@/features/graphs/components/GraphMinActionsDistribution.vue";
import GraphDifficultyVsMinActions from "@/features/graphs/components/GraphDifficultyVsMinActions.vue";
</script>

<template>
  <div class="grid grid-cols-4 gap-2">
    <!-- header -->
    <Container class="text-center text-2xl col-span-4">work-in-progress dashboard</Container>

    <!-- puzzle submissions -->
    <TimelinePuzzleSubmissions :num_games="8" class="col-span-4" />
    <GraphSolveTimeDistribution class="col-span-2" />
    <GraphActionCountDistribution class="col-span-2" />
    <GraphMistakeDistribution class="col-span-2" />
    <GraphMinActionsDistribution class="col-span-2" />
    <GraphDifficultyVsMinActions class="col-span-2" />

    <!-- played puzzles -->
    <GraphPlayedHeatmap class="col-span-4" :cell-size="10" :hide-unplayed="true" />
<!--    <GraphClassMetrics class="col-span-2" />-->
  </div>
</template>

<style scoped></style>
