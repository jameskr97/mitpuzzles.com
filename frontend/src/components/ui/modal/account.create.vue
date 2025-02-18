<script setup lang="ts">
////////////////////////////////////////////////////////////////////////////////
// Imports
import { ref } from "vue";
import { z } from "zod";
import { useAuthStore } from "@/store/auth";
// API Imports
import * as allauth from "@/lib/allauth";
import FormDynamicVertical from "@/components/ui/forms/form.dynamic.vertical.vue";

////////////////////////////////////////////////////////////////////////////////
// Data Stores
const auth = useAuthStore();

////////////////////////////////////////////////////////////////////////////////
// Form Variables
const schema = z
  .object({
    username: z.string().min(3, "Username cannot be blank"),
    email: z.string().email("Invalid email address"),
    password: z.string().min(8, "Password must be at least 8 characters"),
    passwordConfirm: z.string(),
  })
  // Ensure the passwords match
  .refine((data) => data.password === data.passwordConfirm, {
    message: "Passwords do not match",
    path: ["passwordConfirm"],
  });

const schema_meta = {
  username: { label: "Username", type: "text" },
  email: { label: "Email", type: "email" },
  password: {
    label: "Password",
    type: "password",
    autocomplete: "new-password",
  },
  passwordConfirm: {
    label: "Password Confirm",
    type: "password",
    autocomplete: "new-password",
  },
};

////////////////////////////////////////////////////////////////////////////////
// Form Variables
const loading = ref(false);
const externalErrors = ref({});

////////////////////////////////////////////////////////////////////////////////
// Form Validation Functions
function onValidSubmit(values: z.infer<typeof schema>) {
  loading.value = true;

  const payload: allauth.AuthInfo = {
    username: values.username,
    password: values.password,
  };

  if (values.email) payload.email = values.email;

  auth
    .signup(payload)
    .catch((err) => (externalErrors.value = err))
    .finally(() => (loading.value = false));
}
</script>

<template>
  <dialog class="modal">
    <div class="modal-box max-w-xs">
      <h3 class="text-lg font-bold">Create Account</h3>
      <div class="divider m-0"></div>
      <FormDynamicVertical
        title="Create an Account"
        :schema="schema"
        :meta="schema_meta"
        :loading="loading"
        :external-errors="externalErrors"
        @submit="onValidSubmit"
      />
    </div>

    <form method="dialog" class="modal-backdrop">
      <button>close</button>
    </form>
  </dialog>
</template>
