<script setup lang="ts">
import CreateAccountModal from "@/components/modal/account.create.vue";
import LoginModal from "@/components/modal/account.login.vue";
</script>

<template>
  <!-- Sidebar Footer -->
  <div class="flex flex-row justify-between gap-2 mt-auto bg-base-200 w-full">
    <button class="btn btn-info grow" onclick="login_modal.showModal()">Log in</button>
    <button class="btn btn-success grow" onclick="create_account_modal.showModal()">Sign up</button>

    <!-- Modals -->
    <LoginModal id="login_modal" />
    <CreateAccountModal id="create_account_modal" />
  </div>
</template>
