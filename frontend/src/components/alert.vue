<script setup lang="ts">
defineProps({
  icon: { type: String, required: false, default: "fa-check-circle" },
  scale: { type: Number, required: false, default: 1.5 },
});
</script>

<template>
  <div role="alert" class="alert flex flex-row justify-start mb-2">
    <v-icon :name="icon" :scale="scale" />
    <span>
      <slot></slot>
    </span>
  </div>
</template>
