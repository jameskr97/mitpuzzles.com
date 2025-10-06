<script setup lang="tsx">
import Container from "@/components/ui/Container.vue";
import AlertEmailAlreadyVerified from "@/components/alert/AlertEmailAlreadyVerified.vue";
import AlertEmailVerifiySuccess from "@/components/alert/AlertEmailVerifiySuccess.vue";
import HomePuzzlePreview from "@/components/HomePuzzlePreview.vue";
import { ACTIVE_GAMES } from "@/constants.ts";
import { useAppStore } from "@/store/useAppStore.ts";
import { useAuthStore } from "@/store/useAuthStore.ts";

const appStore = useAppStore();
const authStore = useAuthStore();
</script>

<template>

  <div class="m-2 gap-2 flex flex-col">
    <AlertEmailAlreadyVerified v-if="$route.query.alreadyVerified" />
    <AlertEmailVerifiySuccess v-if="$route.query.verified" />
    <Container class="grid grid-cols-1">
      <div class="flex flex-col">
        <div class="text-lg">
          <p class="text-center">
            MIT's Computational Cogitive Science Lab wants to
            <span class="font-bold italic text-red-700">understand human reasoning and cognition </span>
            through logic puzzles. Help science and have fun!
          </p>
        </div>
      </div>
    </Container>

    <Container v-if="!authStore.isAuthenticated" class="text-center">
      <p class="text-lg font-semibold text-gray-700 text-center">
          <span class="underline cursor-pointer hover:text-blue-600" @click="appStore.open_login_modal()">Login</span>
          or
          <router-link class="underline cursor-pointer hover:text-blue-600" :to="{ name: 'signup' }">create an account</router-link>
          to track your progress over time!
        </p>
    </Container>
<!--    <HomeUserStatsBar />-->

      <!-- Game Grid -->
      <div class="w-full max-w-4xl mx-auto">
        <div class="grid grid-cols-2 md:grid-cols-3 gap-2 rounded-xl">
          <HomePuzzlePreview
            v-for="game in ACTIVE_GAMES"
            class="rounded"
            :title="game.name"
            :page="game.key"
            :key="game.key"
            :component="game.component"
            :state="game.default"
          />
        </div>
      </div>

    </div>
</template>
