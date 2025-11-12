<template>
  <div class="flex items-center justify-center min-h-screen">
    <div class="flex flex-col gap-2 w-100 text-center">
      <p class="text-5xl">404</p>
      <router-link :to="{ name: 'Home' }" class="link link-primary">{{ $t('ui:error.404_message') }}</router-link>
    </div>
  </div>
</template>
