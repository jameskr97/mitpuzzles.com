<script setup lang="ts">
import { useAppConfig } from '@/store/config';
import { useGameWebSocketStore } from '@/store/gamesocket';
const colors = ['bg-green-500', 'bg-yellow-500', 'bg-red-500', 'bg-blue-500', 'bg-indigo-500', 'bg-purple-500', 'bg-pink-500'];
const settings = useAppConfig();
settings.fetchGameSettings();
</script>

<template>
  <div class="flex p-4 flex-col border border-red-500 rev justify-center">
    <p class="text-3xl">Start a new game</p>
    <hr class="h-px my-2 bg-gray-200 border-0 dark:bg-gray-700" />
    <div class="flex flex-col gap-1">
      <div v-for="(gameinfo, _) in Object.values(settings.games)" class="flex flex-col">
        <!-- Header + Dotted Line -->
        <p class="text-2xl ml-4">{{ gameinfo.displayname }}</p>

        <!-- Body -->
        <div class="grid grid-cols-[70%_30%] h-50">
          <div class="grid grid-cols-2 border-blue-500 bg-[url(https://placehold.co/800x200?text=Wow\\nPlaceholder\\nText)] bg-no-repeat bg-right">
            <!-- Difficulty Selection Body -->
            <div class="flex flex-col w-full overflow-hidden grow-0 rounded-l-2xl">
              <div
                v-for="(item , index) in gameinfo.modes"
                :class="
                  colors[index] + ' z-' + (99-index) +
                  ' shadow-sm skeleton h-full animate-none flex justify-end items-center transition-transform duration-150 ease-in-out hover:translate-x-[10%] -ms-100 me-[30%] transform-flat'
                "
                @click="ws.game_create(gameinfo.key, item.options)"
              >
                <div class="text-4xl translate-x-[-10%] select-none">
                  {{ item.displayname }}
                </div>
              </div>
            </div>
          </div>

          <!-- Scoreboard Body -->
          <div class="border border-green-400 max-h-50 rounded-r-2xl">
            <div class="overflow-x-auto h-50">
              <table class="table table-xs">
                <thead>
                  <tr>
                    <td>#</td>
                    <td>Name</td>
                    <td>Rank</td>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(_, i) in 10">
                    <th>{{ i + 1 }}</th>
                    <td>Cy Ganderton</td>
                    <td>Quality Control</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- End -->
      </div>
    </div>
  </div>
</template>
