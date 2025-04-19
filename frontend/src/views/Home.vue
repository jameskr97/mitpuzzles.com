<script setup lang="tsx">
import HomePuzzlePreview from "@/components/home.puzzlepreview.vue";
import { ACTIVE_GAMES } from "@/main";

import { useAppConfig } from "@/store/config";
import { ref, type Ref } from "vue";
const settings = useAppConfig();
settings.fetchGameSettings();

const game_entries = Object.values(ACTIVE_GAMES);
const puzzleStates: Record<string, Ref<any>> = {};
await Promise.all(
  game_entries.map(async (game) => {
    puzzleStates[game.key] = ref(await game.default());
  }),
);
</script>

<template>
  <div class="text-2xl text-center w-full">Welcome to mitpuzzles.com</div>
  <div class="divider my-0"></div>

  <div class="sm:hidden">
    <div role="alert" class="alert alert-info m-2">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 shrink-0 stroke-current" fill="none" viewBox="0 0 24 24">
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
        />
      </svg>
      <span>
        Thanks for visiting our website! If you're on a mobile-device, keep in mind that not all games will work
        properly through a touch screen.
      </span>
    </div>
    <div class="divider my-0"></div>
  </div>

  <p class="max-w-xl mx-auto text-base">
    Welcome to the first test version of this website! We've made available a limited set of games. For each game you
    play, your actions will be recorded once the game has been submitted and completed correctly. Please try out any of
    the games below - we'd love your help!
  </p>
  <div class="divider my-0"></div>
  <div class="grid grid-cols-2 lg:grid-cols-4 xl:grid-cols-5 gap-3 mx-auto">
    <HomePuzzlePreview
      v-for="game in game_entries"
      class="border-2 rounded border-gray-400"
      :title="game.name"
      :page="game.key"
      :key="game.key"
      :component="game.component"
      :state="puzzleStates[game.key]"
    />
  </div>
</template>
