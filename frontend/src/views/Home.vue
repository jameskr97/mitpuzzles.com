<script setup lang="tsx">
import Container from "@/core/components/ui/Container.vue";
import AlertEmailAlreadyVerified from "@/core/components/alert/AlertEmailAlreadyVerified.vue";
import AlertEmailVerifiySuccess from "@/core/components/alert/AlertEmailVerifiySuccess.vue";
import HomePuzzlePreview from "@/core/components/HomePuzzlePreview.vue";
import HomeDailyPreview from "@/core/components/HomeDailyPreview.vue";
import { ACTIVE_GAMES } from "@/constants.ts";
import { useAuthStore } from "@/core/store/useAuthStore.ts";
import EmailVerificationBanner from "@/core/components/EmailVerificationBanner.vue";
import DemographicBanner from "@/core/components/DemographicBanner.vue";
import { computed } from "vue";
import NewsFeed from "@/core/components/NewsFeed.vue";
import CreateAccountCTA from "@/core/components/alert/CreateAccountCTA.vue";
import DailyLeaderboardCompact from "@/features/daily/DailyLeaderboardCompact.vue";

const authStore = useAuthStore();
const is_dev = import.meta.env.DEV;
const visible_games = computed(() =>
  Object.values(ACTIVE_GAMES).filter((g) => !g.admin_only || authStore.isAdmin || is_dev),
);
</script>

<template>
  <div class="flex flex-col gap-2 max-w-7xl mx-auto">
    <EmailVerificationBanner data-testid="banner-email-verify" />
    <DemographicBanner />
    <AlertEmailAlreadyVerified v-if="$route.query.alreadyVerified" data-testid="banner-email-already-verified" />
    <AlertEmailVerifiySuccess v-if="$route.query.verified" data-testid="banner-email-successfully-verified" />
    <CreateAccountCTA v-if="!authStore.isAuthenticated" />

    <!-- welcome banner -->
    <Container class="h-min">
      <div class="text-lg">
        <p class="text-center" v-html="$t('home:welcome_message')"></p>
      </div>
    </Container>

    <!-- puzzle grid: 4 columns -->
    <div class="grid grid-cols-2 md:grid-cols-4 w-full gap-2">
      <div class="grid grid-cols-subgrid col-span-4 grid-rows-1">
        <HomeDailyPreview />
        <DailyLeaderboardCompact class="min-h-0 overflow-hidden" />
        <NewsFeed class="overflow-hidden h-0 min-h-full col-span-2" />
      </div>

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
</template>
