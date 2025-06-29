<script setup lang="ts">
import SudokuExperiment from "@/features/prolific.experiments/2025.05.29.sudoku/ExperimentMain.vue";
import { onMounted } from "vue";
import { useGameService } from "@/services/game/useGameService.ts";

const ensure_prolific = () => {
  if (ws.identity_mode !== "prolific") {
    console.log("reloading")
    location.reload();
    ws.bus.off("connected", ensure_prolific);
  }
};

const ws = useGameService();
onMounted((x) => {
  console.log("mounted test-experiment");
  console.log(ws.connected.value)
  if (ws.connected.value) {
    console.log("already connected");
    ensure_prolific();
  } else {
    ws.bus.on("connected", ensure_prolific);
  }
});
</script>

<template>
  <SudokuExperiment />
</template>
