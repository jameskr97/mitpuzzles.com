<script setup lang="ts">
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { useCurrentPuzzle } from "@/composables/useCurrentPuzzle.ts";

const puzzle = await useCurrentPuzzle();
</script>

<template>

</template>
