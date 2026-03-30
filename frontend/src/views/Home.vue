<script setup lang="tsx">
import Container from "@/core/components/ui/Container.vue";
import AlertEmailAlreadyVerified from "@/core/components/alert/AlertEmailAlreadyVerified.vue";
import AlertEmailVerifiySuccess from "@/core/components/alert/AlertEmailVerifiySuccess.vue";
import HomePuzzlePreview from "@/core/components/HomePuzzlePreview.vue";
import { ACTIVE_GAMES } from "@/constants.ts";
import { useAppStore } from "@/core/store/useAppStore.ts";
import { useAuthStore } from "@/core/store/useAuthStore.ts";
import EmailVerificationBanner from "@/core/components/EmailVerificationBanner.vue";
import DemographicBanner from "@/core/components/DemographicBanner.vue";
import { Button } from "@/core/components/ui/button";
import { useDailyPuzzleStore } from "@/core/store/puzzle/useDailyPuzzleStore.ts";
import { computed } from "vue";
import NewsFeed from "@/core/components/NewsFeed.vue";
import CreateAccountCTA from "@/core/components/alert/CreateAccountCTA.vue";

const authStore = useAuthStore();
const dailyStore = useDailyPuzzleStore();
const is_dev = import.meta.env.DEV;
const visible_games = computed(() =>
  Object.values(ACTIVE_GAMES).filter(g => !g.admin_only || authStore.isAdmin || is_dev)
);
</script>

<template>
  <div class="flex flex-col gap-2">
    <EmailVerificationBanner data-testid="banner-email-verify" />
    <DemographicBanner />
    <AlertEmailAlreadyVerified v-if="$route.query.alreadyVerified" data-testid="banner-email-already-verified" />
    <AlertEmailVerifiySuccess v-if="$route.query.verified" data-testid="banner-email-successfully-verified" />
    <CreateAccountCTA v-if="!authStore.isAuthenticated" />

    <!-- 2-column homepage   -->
    <div class="w-full grid grid-cols-[1fr_0.5fr] gap-2 mx-auto">
      <!-- column 1: welcome banner + game grid -->
      <div class="flex flex-col gap-2">
        <Container class="grid grid-cols-1 h-min">
          <div class="flex flex-col">
            <div class="text-lg">
              <p class="text-center" v-html="$t('home:welcome_message')"></p>
            </div>
          </div>
        </Container>
        <div class="grid grid-cols-2 md:grid-cols-3 w-full gap-2 rounded-xl">
          <HomePuzzlePreview title="Daily Puzzle" page="daily">
            <span class="text-8xl">🗓️</span>
          </HomePuzzlePreview>
          <HomePuzzlePreview
            v-for="game in visible_games"
            class="rounded"
            :title="game.name"
            :page="game.key"
            :key="game.key"
            :component="game.component"
            :state="game.default"
          />
        </div>
      </div>

      <!-- column 2: newsfeed -->
      <NewsFeed />
    </div>
  </div>
</template>
