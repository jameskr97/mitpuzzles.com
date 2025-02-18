<script setup lang="ts">
////////////////////////////////////////////////////////////////////////////////
// Imports
import FormDynamicVertical from "@/components/ui/forms/form.dynamic.vertical.vue";
import { useAuthStore } from "@/store/auth";
import { ref } from "vue";
import { z } from "zod";
// API Imports
import * as allauth from "@/lib/allauth";

////////////////////////////////////////////////////////////////////////////////
// Data Stores
const auth = useAuthStore();

////////////////////////////////////////////////////////////////////////////////
// Form Variables
const schema = z.object({
  email: z.string().email("Invalid email address"),
  password: z.string(),
});

const schema_meta = {
  email: { label: "Email", type: "email", autocomplete: "email" },
  password: {
    label: "Password",
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
    email: values.email,
    password: values.password,
  };

  if (values.email) payload.email = values.email;

  auth
    .login(payload)
    .catch((err) => (externalErrors.value = err))
    .finally(() => (loading.value = false));
}
</script>

<template>
  <dialog class="modal" role="dialog">
    <div class="modal-box max-w-xs">
      <h3 class="text-lg font-bold">Login</h3>
      <div class="divider m-0"></div>
      <FormDynamicVertical
        title="Login"
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
