<script setup lang="tsx">
import HomePuzzlePreview from "@/components/home.puzzlepreview.vue";
import { ACTIVE_GAMES } from "@/constants";
import { useVisitorStore } from "@/store/visitor.ts";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import Container from "@/components/ui/Container.vue";
import { useAppConfig } from "@/store/app.ts";

const visitor = useVisitorStore();
const app = useAppConfig();
</script>

<template>
  <Alert class="m-2 sm:hidden">
    <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 shrink-0 stroke-current" fill="none" viewBox="0 0 24 24">
      <path
        stroke-linecap="round"
        stroke-linejoin="round"
        stroke-width="2"
        d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
      />
    </svg>
    <AlertTitle>Welcome mobile user!</AlertTitle>
    <AlertDescription>
      Thanks for visiting our website! If you're on a mobile-device, keep in mind that not all games will work properly
      through a touch screen.
    </AlertDescription>
  </Alert>

  <Container class="p-2 mt-2">
    <div class="flex flex-col gap-3 p-3">
      <p class="text-3xl">Welcome to an alpha version of <span class="font-bold">mitpuzzles.com</span>.</p>
      <div class="text-lg">
        <p>
          Help with cognitive science research by playing logic puzzles! Please try out any of the games below - we'd
          love your help!
        </p>
        <p>
          Your username is <span class="font-bold">{{ visitor.generated_username }}</span> and can be changed from the
          sidebar.
        </p>
        <p>
          Current RTT: {{ app.rtt || '??' }}ms.
        </p>
      </div>
    </div>
  </Container>
  <div class="grid grid-cols-3 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-2 mx-auto mt-2">
    <HomePuzzlePreview
      v-for="game in ACTIVE_GAMES"
      class="border rounded shadow border-gray-300"
      :title="game.name"
      :page="game.key"
      :key="game.key"
      :component="game.component"
      :state="game.default"
    />
  </div>
</template>
