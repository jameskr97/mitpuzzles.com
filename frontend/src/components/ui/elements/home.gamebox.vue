<script setup lang="ts">

defineProps({
  title: { type: String, required: true },
});

</script>

<template>
    <div class="aspect-square">
        <slot></slot>
        <p class="text-2xl mt-1 w-full text-center">{{ title }}</p>
    </div>
</template>