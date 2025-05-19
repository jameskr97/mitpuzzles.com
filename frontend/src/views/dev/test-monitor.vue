<script setup lang="ts">
import {useActivePuzzleStore, usePuzzleSocket} from "@/features/games.composables/usePuzzleSocket.ts";
import {computed, onMounted, onUnmounted, ref} from "vue";
import { ACTIVE_GAMES } from "@/main.ts";
import { remap } from "@/services/util.ts";

const socket = usePuzzleSocket();
const active_store = useActivePuzzleStore();
const active_msg = computed(() => {
  const count = active_store.monitor_user_count;
  return `${count} Active User${count === 1 ? "" : "s"}`;
});

const scale = ref(50);
const scale_remapped = computed(() => remap([0, 100], [1, 3], scale.value));
onMounted(() => socket.cmd_puzzle_monitor())
onUnmounted(() => socket.cmd_puzzle_unmonitor())
</script>

<template>
  <div>
    <div class="flex flex-row">
      <div class="absolute flex-none">{{ active_msg }}</div>
      <div class="text-2xl text-center w-full grow">Test Game Monitoring</div>
    </div>
    <div class="divider my-0"></div>
    <input v-model="scale" type="range" min="0" max="100" class="range w-full" />
    <div class="divider my-0"></div>
    <div class="grid grid-cols-3 gap-2">
      <div v-for="(game, key) in active_store.monitored_users_games" class="flex flex-col border rounded shadow">
        <div class="@container aspect-square place-items-center grid select-none pointer-events-none">
          <component :is="ACTIVE_GAMES[game.puzzle_type].component" :state="game" :scale="scale_remapped" />
        </div>
        <div class="divider my-0 py-0 h-full"></div>
        <div class="p-1 mx-auto">{{ key }}</div>
      </div>
    </div>
  </div>
</template>
