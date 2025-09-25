<script setup lang="ts">
import { ref, computed } from "vue";
import { useRouter } from "vue-router";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuthStore } from "@/store/useAuthStore.ts";
import { useAppStore } from "@/store/useAppStore.ts";

const auth = useAuthStore();
const appStore = useAppStore();
const router = useRouter();

// Form fields
const email = ref("");
const password = ref("");

// Form validation
const isFormValid = computed(() => {
  return email.value && password.value && email.value.includes("@");
});

// Clear error when user starts typing
const clearErrorOnInput = () => {
  if (auth.error) {
    auth.clearError();
  }
};

// Computed property for display error message
const displayError = computed(() => {
  if (!auth.error) return null;
  if (auth.error === "LOGIN_BAD_CREDENTIALS") return "Invalid email or password. Please try again.";
  return auth.error;
});

// Handle login submission
const handleLogin = async () => {
  if (!isFormValid.value) return;

  try {
    await auth.login({ email: email.value, password: password.value });
    // invariant - login success
    // Success - close modal and redirect
    appStore.close_login_modal(); // close modal
    email.value = ""; // reset form
    password.value = "";
    await router.push("/"); // redirect homepage
  } catch (error) {
    console.error("Login failed:", error);
  }
};
</script>

<template>
  <Dialog v-model:open="appStore.login_modal_open">
    <DialogTrigger>
      <slot></slot>
    </DialogTrigger>
    <DialogContent as-child>
      <Card class="mx-auto sm:max-w-[400px]">
        <CardHeader>
          <CardTitle class="text-2xl">Login</CardTitle>
          <CardDescription> Enter your email below to login to your account </CardDescription>
        </CardHeader>
        <CardContent>
          <form @submit.prevent="handleLogin" class="grid gap-4">
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
                :disabled="auth.loading"
              />
            </div>

            <!-- Password -->
            <div class="grid gap-2">
              <div class="flex items-center">
                <Label for="password">Password</Label>
                <a href="#" class="ml-auto inline-block text-sm underline"> Forgot your password? </a>
              </div>
              <Input
                id="password"
                v-model="password"
                type="password"
                required
                @input="clearErrorOnInput"
                :disabled="auth.loading"
              />
            </div>

            <!-- Error Display -->
            <div v-if="displayError" class="text-sm text-red-600 bg-red-50 border border-red-200 rounded p-3">
              {{ displayError }}
            </div>

            <!-- Actions -->
            <Button type="submit" class="w-full" :disabled="!isFormValid || auth.loading">
              <div v-if="auth.loading" class="flex items-center gap-2">
                <div class="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin"></div>
                Logging in...
              </div>
              <span v-else>Login</span>
            </Button>
          </form>
          <Button variant="outline" class="w-full mt-2" :disabled="auth.loading" @click="auth.social_login('google')">
            Login with Google
          </Button>

          <div class="mt-4 text-center text-sm">
            <span class="mr-1">Don't have an account?</span>
            <router-link :to="{ name: 'signup' }">
              <span class="underline">Sign Up</span>
            </router-link>
          </div>
        </CardContent>
      </Card>
    </DialogContent>
  </Dialog>
</template>
