<script setup lang="ts">
import { computed, ref, onMounted } from "vue";
import { useAuthStore } from "@/store/useAuthStore";
import { useRoute, useRouter } from "vue-router";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { X } from "lucide-vue-next";
import axios from "axios";

const DISMISSED_KEY = "mitlogic.banner.demographic_dismissed";

const auth_store = useAuthStore();
const route = useRoute();
const router = useRouter();

const is_dismissed = ref(false);
const profile = ref<any>(null);
const is_loading = ref(false);

const is_profile_incomplete = computed(() => {
  if (!profile.value) return true;

  const has_basic_info = profile.value.age &&
                         profile.value.gender &&
                         profile.value.education_level;

  const has_game_experience = profile.value.game_experience &&
                              Object.keys(profile.value.game_experience).length > 0;

  return !has_basic_info || !has_game_experience;
});

const should_show_banner = computed(() => {
  const is_homepage = route.name === "Home";
  return is_homepage &&
         auth_store.isAuthenticated &&
         !is_dismissed.value &&
         is_profile_incomplete.value;
});

const fetch_profile = async () => {
  if (!auth_store.isAuthenticated) return;

  is_loading.value = true;
  try {
    const response = await axios.get("/api/profile/me");
    profile.value = response.data;
  } catch (error) {
    console.error("Failed to fetch profile:", error);
  } finally {
    is_loading.value = false;
  }
};

const dismiss_banner = () => {
  localStorage.setItem(DISMISSED_KEY, "true");
  is_dismissed.value = true;
};

const navigate_to_profile = () => {
  router.push({ name: "account" });
};

onMounted(() => {
  // Check if banner was previously dismissed
  is_dismissed.value = localStorage.getItem(DISMISSED_KEY) === "true";

  // Fetch profile to check completeness
  fetch_profile();
});
</script>

<template>
  <Alert v-if="should_show_banner" variant="info" class="mb-0 relative">
    <AlertDescription class="flex items-center justify-between pr-8">
      <span>
        <strong>{{ $t('ui:banner.demographic_title') }}</strong> {{ $t('ui:banner.demographic_message') }}
      </span>
      <Button
        variant="outline"
        size="sm"
        @click="navigate_to_profile"
        class="bg-white"
      >
        {{ $t('ui:banner.complete_profile') }}
      </Button>

      <!-- Close button -->
      <button
        @click="dismiss_banner"
        class="absolute top-3 right-3 p-1 rounded-sm opacity-70 hover:opacity-100 transition-opacity"
        :aria-label="$t('ui:banner.dismiss')"
      >
        <X class="h-4 w-4" />
      </button>
    </AlertDescription>
  </Alert>
</template>
