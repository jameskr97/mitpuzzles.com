<script setup lang="ts">
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { computed, ref } from "vue";
import { useAuthStore } from "@/store/useAuthStore.ts";
import AppLogo from "@/components/AppLogo.vue";

// Form Related Fields
const username = ref("");
const email = ref("");
const password = ref("");
const passwordVerify = ref("");
const registrationSuccess = ref(false);

// Clear error when user starts typing
const clearErrorOnInput = () => {
  if (authStore.error) {
    authStore.clearError();
  }
};
const emailError = computed(() => {
  if (!email.value) return "";
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email.value) ? "" : "Please enter a valid email address";
});
const passwordMatchError = computed(() => {
  if (!password.value || !passwordVerify.value) return "";
  return password.value === passwordVerify.value ? "" : "Passwords do not match";
});
const isFormValid = computed(() => {
  return (
    username.value &&
    email.value &&
    !emailError.value &&
    password.value &&
    passwordVerify.value &&
    !passwordMatchError.value
  );
});

// Submission Field
const authStore = useAuthStore();
const submitForm = async () => {
  try {
    const res = await authStore.register({ username: username.value, email: email.value, password: password.value });
    // Handle successful registration (e.g., redirect to dashboard)
    console.log("Registration successful", res);
    registrationSuccess.value = true;
  } catch (error) {
    // Error is already stored in authStore.error
    console.error("Registration error:", error);
  }
};
</script>
<template>
  <div class="flex flex-col h-full w-full items-center justify-center p-4">
    <Card v-if="!registrationSuccess" class="mx-auto md:w-[400px] w-full">
      <CardHeader class="text-center">
        <AppLogo class="w-80 mb-4 mx-auto" />
        <Separator />
        <CardTitle class="text-2xl"> Sign Up </CardTitle>

        <CardDescription>Enter your information to create an account </CardDescription>
      </CardHeader>
      <CardContent>
        <form @submit.prevent="submitForm">
          <div class="grid gap-4">
            <!-- Username -->
            <div class="grid gap-2">
              <Label for="username">Username</Label>
              <Input
                id="username"
                v-model="username"
                placeholder="John"
                autocomplete="username"
                required
                @input="clearErrorOnInput"
                :disabled="authStore.loading"
              />
            </div>

            <!-- Email -->
            <div class="grid gap-2">
              <Label for="email">Email</Label>
              <Input
                id="email"
                v-model="email"
                type="email"
                placeholder="user@example.com"
                required
                @input="clearErrorOnInput"
                :disabled="authStore.loading"
              />
              <div v-if="emailError" class="text-sm text-red-600">{{ emailError }}</div>
            </div>

            <!-- Password -->
            <div class="grid gap-2">
              <Label for="password">Password</Label>
              <Input
                id="password"
                v-model="password"
                type="password"
                autocomplete="new-password"
                required
                @input="clearErrorOnInput"
                :disabled="authStore.loading"
              />
            </div>

            <!-- Password Verify -->
            <div class="grid gap-2">
              <Label for="password-verify">Password Verify</Label>
              <Input
                id="password-verify"
                v-model="passwordVerify"
                type="password"
                autocomplete="new-password"
                required
                :disabled="authStore.loading"
              />
              <div v-if="passwordMatchError" class="text-sm text-red-600">{{ passwordMatchError }}</div>
            </div>

            <!-- Registration Error -->
            <div v-if="authStore.error" class="text-sm text-red-600 bg-red-50 border border-red-200 rounded p-3">
              <span v-if="authStore.error == 'REGISTER_USER_ALREADY_EXISTS'">
                A user with that email already exists.
              </span>
              <span v-if="authStore.error == 'REGISTER_INVALID_PASSWORD'">
                {{ authStore.error }}
              </span>
              <span v-else>
                {{ authStore.error }}
              </span>
            </div>

            <Button type="submit" class="w-full" :disabled="!isFormValid || authStore.loading">
              <div v-if="authStore.loading" class="flex items-center gap-2">
                <div class="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin"></div>
                Creating account...
              </div>
              <span v-else>Create an account</span>
            </Button>
            <Button variant="outline" class="w-full" @click="authStore.social_login('google')" :disabled="authStore.loading">Sign up with Google</Button>
          </div>
        </form>

        <div class="mt-4 text-center text-sm">
          Already have an account?
          <a href="#" class="underline"> Sign in </a>
        </div>
      </CardContent>
    </Card>

    <Card v-else class="mx-auto md:w-[400px] w-full">
      <CardHeader class="text-center">
        <CardTitle class="text-xl"> Registration Complete! </CardTitle>
        <CardDescription>
          <div
            v-if="registrationSuccess"
            class="text-sm text-black bg-green-100 border border-green-300 rounded-xl p-3"
          >
            <p>
              Almost done! We've sent a verification email to <span class="font-bold">{{ email }}</span
              >. Please click the link in the email to complete your registration.
            </p>
          </div>
        </CardDescription>
      </CardHeader>
    </Card>
  </div>
</template>
