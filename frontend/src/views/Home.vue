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

const appStore = useAppStore();
const authStore = useAuthStore();
</script>

<template>
  <div class="flex flex-col gap-2 ">
    <EmailVerificationBanner data-testid="banner-email-verify" />
    <DemographicBanner />
    <AlertEmailAlreadyVerified v-if="$route.query.alreadyVerified" data-testid="banner-email-already-verified" />
    <AlertEmailVerifiySuccess v-if="$route.query.verified" data-testid="banner-email-successfully-verified" />
    <Container class="grid grid-cols-1">
      <div class="flex flex-col">
        <div class="text-lg">
          <p class="text-center" v-html="$t('home:welcome_message')"></p>
        </div>
      </div>
    </Container>

    <Container v-if="!authStore.isAuthenticated" class="w-full justify-center text-lg font-semibold text-gray-700 mb-2 flex flex-col md:flex-row mx-auto items-center">
        <span>{{ $t('home:track_progress_prompt') }}</span>
        <div class="flex gap-2 ml-2">
          <Button @click="appStore.open_login_modal()">
            {{ $t('home:login_action') }}
          </Button>
          <router-link :to="{ name: 'signup' }">
            <Button>
              {{ $t('home:signup_action') }}
            </Button>
          </router-link>
        </div>
    </Container>
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
