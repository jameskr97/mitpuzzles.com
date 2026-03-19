<script setup lang="ts">
import { Button } from "@/core/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/core/components/ui/card";
import { Input } from "@/core/components/ui/input";
import { Label } from "@/core/components/ui/label";
import { Separator } from "@/core/components/ui/separator";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/core/components/ui/select";
import { Switch } from "@/core/components/ui/switch";
import { computed, onMounted, ref } from "vue";
import { useAuthStore } from "@/core/store/useAuthStore.ts";
import { usePushStore } from "@/core/store/usePushStore.ts";
import { ACTIVE_GAMES } from "@/constants.ts";
import { api } from "@/core/services/client";
import { useTranslation } from "i18next-vue";
import { capture_event } from "@/core/services/posthog.ts";

const { t } = useTranslation();

const auth_store = useAuthStore();

// Username form
const new_username = ref(auth_store.user?.username || "");
const username_loading = ref(false);
const username_success = ref(false);
const username_error = ref("");

// Password form
const current_password = ref("");
const new_password = ref("");
const confirm_password = ref("");
const password_loading = ref(false);
const password_success = ref(false);
const password_error = ref("");

// Validation
const password_match_error = computed(() => {
  if (!new_password.value || !confirm_password.value) return "";
  return new_password.value === confirm_password.value ? "" : t("ui:validation.password_mismatch");
});

const is_username_changed = computed(() => {
  return new_username.value !== auth_store.user?.username;
});

const is_username_valid = computed(() => {
  return new_username.value.trim().length > 0 && is_username_changed.value;
});

const is_password_valid = computed(() => {
  return current_password.value && new_password.value && confirm_password.value && !password_match_error.value;
});

// Submit handlers
const submit_username = async () => {
  username_loading.value = true;
  username_success.value = false;
  username_error.value = "";

  const result = await auth_store.updateUsername(new_username.value);
  username_loading.value = false;

  if (!result) {
    username_error.value = auth_store.error || "Failed to update username";
    return;
  }

  username_success.value = true;
  setTimeout(() => { username_success.value = false; }, 3000);
};

const submit_password = async () => {
  password_loading.value = true;
  password_success.value = false;
  password_error.value = "";

  const result = await auth_store.update_password(current_password.value, new_password.value);
  password_loading.value = false;

  if (!result) {
    password_error.value = auth_store.error || "Failed to update password";
    return;
  }

  password_success.value = true;
  current_password.value = "";
  new_password.value = "";
  confirm_password.value = "";
  setTimeout(() => { password_success.value = false; }, 3000);
};

// Profile form
const profile_age = ref<number | null>(null);
const profile_gender = ref("");
const profile_education_level = ref("");
const profile_game_experience = ref<Record<string, string>>({});
const profile_loading = ref(false);
const profile_success = ref(false);
const profile_error = ref("");

const game_types = Object.keys(ACTIVE_GAMES);

const fetch_profile = async () => {
  const { data: profile, error } = await api.GET("/api/profile/me");
  if (error) return;

  if (profile.age) profile_age.value = profile.age;
  if (profile.gender) profile_gender.value = profile.gender;
  if (profile.education_level) profile_education_level.value = profile.education_level;
  if (profile.game_experience) profile_game_experience.value = profile.game_experience;
};

const submit_profile = async () => {
  profile_loading.value = true;
  profile_success.value = false;
  profile_error.value = "";

  const { error } = await api.PATCH("/api/profile/me", {
    body: {
      age: profile_age.value || null,
      gender: profile_gender.value || null,
      education_level: profile_education_level.value || null,
      game_experience: profile_game_experience.value,
    },
  });

  profile_loading.value = false;

  if (error) {
    profile_error.value = (error as any)?.detail || "Failed to update profile";
  } else {
    profile_success.value = true;
    setTimeout(() => { profile_success.value = false; }, 3000);
  }
};

// Push notifications
const push_store = usePushStore();

const toggle_notifications = async (enabled: boolean | Event) => {
  // Request permission IMMEDIATELY - must be first line for user gesture context
  const permissionPromise =
    Notification.permission === "default" ? Notification.requestPermission() : Promise.resolve(Notification.permission);

  // Handle if event is passed instead of boolean
  const isEnabled = typeof enabled === "boolean" ? enabled : (enabled as any).target?.checked;
  if (isEnabled) {
    const permission = await permissionPromise;

    if (permission !== "granted") {
      push_store.error = "Notification permission denied";
      capture_event("push_permission_denied");
      return;
    }

    const success = await push_store.subscribe();
    if (success) {
      capture_event("push_subscribed");
    }
  } else {
    const success = await push_store.unsubscribe();
    if (success) {
      capture_event("push_unsubscribed");
    }
  }
};

onMounted(() => {
  fetch_profile();
  push_store.check_subscription_status();
});
</script>

<template>
  <div class="flex flex-col h-full w-full p-6 max-w-4xl mx-auto">
    <div class="mb-6 text-center">
      <h1 class="text-3xl font-bold">{{ $t('account:title') }}</h1>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-2">
      <!-- Profile Section -->
      <Card>
        <CardHeader>
          <CardTitle>{{ $t('account:profile.title') }}</CardTitle>
          <CardDescription>{{ $t('account:profile.description') }}</CardDescription>
        </CardHeader>
        <CardContent>
          <form @submit.prevent="submit_username">
            <div class="flex items-start gap-6">
              <div class="flex-1 space-y-4">
                <div class="grid gap-2">
                  <Label for="username">{{ $t('ui:form.username') }}</Label>
                  <Input
                    id="username"
                    v-model="new_username"
                    :placeholder="$t('account:profile.username_placeholder')"
                    autocomplete="username"
                    :disabled="username_loading"
                    @input="username_error = ''"
                  />
                </div>

                <!-- Success Message -->
                <div
                  v-if="username_success"
                  class="text-sm text-green-600 bg-green-50 border border-green-200 rounded p-3"
                >
                  {{ $t('account:profile.success') }}
                </div>

                <!-- Error Message -->
                <div v-if="username_error" class="text-sm text-red-600 bg-red-50 border border-red-200 rounded p-3">
                  {{ username_error }}
                </div>

                <Button type="submit" :disabled="!is_username_valid || username_loading">
                  <div v-if="username_loading" class="flex items-center gap-2">
                    <div class="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin"></div>
                    {{ $t('ui:action.updating') }}
                  </div>
                  <span v-else>{{ $t('account:profile.update_username') }}</span>
                </Button>

                <Separator />

                <!-- Notifications -->
                <div class="space-y-4">
                  <div class="flex items-center justify-between">
                    <div class="space-y-0.5">
                      <Label for="push-notifications" class="text-base">{{ $t('account:push.title') }}</Label>
                      <p class="text-sm text-muted-foreground" v-html="$t('account:push.description')"></p>
                    </div>
                    <Switch
                      id="push-notifications"
                      v-model="push_store.is_subscribed"
                      @update:modelValue="toggle_notifications"
                      :disabled="!push_store.is_supported || push_store.is_loading"
                    />
                  </div>

                  <!-- Not supported message -->
                  <div
                    v-if="!push_store.is_supported"
                    class="text-sm text-yellow-600 bg-yellow-50 border border-yellow-200 rounded p-3"
                  >
                    {{ $t('account:push.not_supported') }}
                  </div>

                  <!-- Error Message -->
                  <div v-if="push_store.error" class="text-sm text-red-600 bg-red-50 border border-red-200 rounded p-3">
                    {{ push_store.error }}
                  </div>
                </div>
              </div>
            </div>
          </form>
        </CardContent>
      </Card>

      <!-- Password Section -->
      <Card>
        <CardHeader>
          <CardTitle>{{ $t('account:password.title') }}</CardTitle>
          <CardDescription>{{ $t('account:password.description') }}</CardDescription>
        </CardHeader>
        <CardContent>
          <form @submit.prevent="submit_password">
            <div class="space-y-4">
              <div class="grid gap-2">
                <Label for="current-password">{{ $t('account:password.current') }}</Label>
                <Input
                  id="current-password"
                  v-model="current_password"
                  type="password"
                  autocomplete="current-password"
                  :disabled="password_loading"
                  @input="password_error = ''"
                />
              </div>

              <Separator />

              <div class="grid gap-2">
                <Label for="new-password">{{ $t('account:password.new') }}</Label>
                <Input
                  id="new-password"
                  v-model="new_password"
                  type="password"
                  autocomplete="new-password"
                  :disabled="password_loading"
                  @input="password_error = ''"
                />
              </div>

              <div class="grid gap-2">
                <Label for="confirm-password">{{ $t('account:password.confirm') }}</Label>
                <Input
                  id="confirm-password"
                  v-model="confirm_password"
                  type="password"
                  autocomplete="new-password"
                  :disabled="password_loading"
                />
                <div v-if="password_match_error" class="text-sm text-red-600">
                  {{ password_match_error }}
                </div>
              </div>

              <!-- Success Message -->
              <div
                v-if="password_success"
                class="text-sm text-green-600 bg-green-50 border border-green-200 rounded p-3"
              >
                {{ $t('account:password.success') }}
              </div>

              <!-- Error Message -->
              <div v-if="password_error" class="text-sm text-red-600 bg-red-50 border border-red-200 rounded p-3">
                {{ password_error }}
              </div>

              <Button type="submit" :disabled="!is_password_valid || password_loading">
                <div v-if="password_loading" class="flex items-center gap-2">
                  <div class="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin"></div>
                  {{ $t('ui:action.updating') }}
                </div>
                <span v-else>{{ $t('account:password.change') }}</span>
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      <!-- Profile Information Section -->
      <Card class="col-span-1 md:col-span-2">
        <CardHeader>
          <CardTitle>{{ $t('account:profile_info.title') }}</CardTitle>
        </CardHeader>
        <CardContent>
          <form @submit.prevent="submit_profile">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
              <div class="flex flex-col gap-4">
                <!-- Age -->
                <div class="grid gap-2">
                  <Label for="age">{{ $t('ui:form.age') }}</Label>
                  <Input
                    id="age"
                    :model-value="profile_age ?? undefined"
                    @update:model-value="profile_age = $event ? Number($event) : null"
                    type="number"
                    min="1"
                    max="120"
                    class="w-20"
                    :disabled="profile_loading"
                    @input="profile_error = ''"
                  />
                </div>

                <!-- Gender -->
                <div class="grid gap-2">
                  <Label for="gender">{{ $t('ui:form.gender') }}</Label>
                  <Select v-model="profile_gender" :disabled="profile_loading">
                    <SelectTrigger id="gender">
                      <SelectValue :placeholder="$t('ui:placeholder.select_gender')" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="male">{{ $t('ui:option.gender.male') }}</SelectItem>
                      <SelectItem value="female">{{ $t('ui:option.gender.female') }}</SelectItem>
                      <SelectItem value="non-binary">{{ $t('ui:option.gender.non_binary') }}</SelectItem>
                      <SelectItem value="prefer-not-to-say">{{ $t('ui:option.gender.prefer_not_to_say') }}</SelectItem>
                      <SelectItem value="other">{{ $t('ui:option.gender.other') }}</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <!-- Education Level -->
                <div class="grid gap-2">
                  <Label for="education">{{ $t('ui:form.education_level') }}</Label>
                  <Select v-model="profile_education_level" :disabled="profile_loading">
                    <SelectTrigger id="education">
                      <SelectValue :placeholder="$t('ui:placeholder.select_education')" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="high-school">{{ $t('ui:option.education.high_school') }}</SelectItem>
                      <SelectItem value="some-college">{{ $t('ui:option.education.some_college') }}</SelectItem>
                      <SelectItem value="bachelors">{{ $t('ui:option.education.bachelors') }}</SelectItem>
                      <SelectItem value="masters">{{ $t('ui:option.education.masters') }}</SelectItem>
                      <SelectItem value="phd">{{ $t('ui:option.education.phd') }}</SelectItem>
                      <SelectItem value="other">{{ $t('ui:option.education.other') }}</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div class="grid gap-2">
                <Label class="text-sm max-h-fit">{{ $t('account:profile_info.game_experience') }}</Label>
                <p class="text-sm text-muted-foreground">
                  {{ $t('account:profile_info.experience_prompt') }}
                </p>
                <div v-for="game_key in game_types" :key="game_key" class="grid grid-cols-2 gap-3 items-center">
                  <Label :for="`exp-${game_key}`" class="text-sm font-normal">
                    {{ ACTIVE_GAMES[game_key].icon }} {{ ACTIVE_GAMES[game_key].name }}
                  </Label>
                  <Select v-model="profile_game_experience[game_key]" :disabled="profile_loading" class="w-full">
                    <SelectTrigger :id="`exp-${game_key}`" class="h-9">
                      <SelectValue :placeholder="$t('ui:placeholder.prior_games')" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="0">{{ $t('ui:option.experience.zero') }}</SelectItem>
                      <SelectItem value="1-5">{{ $t('ui:option.experience.one_to_five') }}</SelectItem>
                      <SelectItem value="5-50">{{ $t('ui:option.experience.five_to_fifty') }}</SelectItem>
                      <SelectItem value="50+">{{ $t('ui:option.experience.fifty_plus') }}</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </div>
            <div class="flex flex-col gap-2 mt-6">
              <!-- Success Message -->
              <div
                v-if="profile_success"
                class="text-sm text-green-600 bg-green-50 border border-green-200 rounded p-3"
              >
                {{ $t('account:profile_info.success') }}
              </div>

              <!-- Error Message -->
              <div v-if="profile_error" class="text-sm text-red-600 bg-red-50 border border-red-200 rounded p-3">
                {{ profile_error }}
              </div>

              <Button type="submit" :disabled="profile_loading">
                <div v-if="profile_loading" class="flex items-center gap-2">
                  <div class="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin"></div>
                  {{ $t('ui:action.saving') }}
                </div>
                <span v-else>{{ $t('account:profile_info.save') }}</span>
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  </div>
</template>
