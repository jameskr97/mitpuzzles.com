<script setup lang="ts">
defineProps({
  loading: {
    type: Boolean,
    required: false,
    default: false,
  }
}

);
</script>

<template>
  <button>
    <slot v-if="!loading"></slot>
    <span v-if="loading" class="loading loading-dots loading-md"></span>
  </button>
</template>
