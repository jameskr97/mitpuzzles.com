<script setup lang="ts">
</script>

<template>
  <div>
    <div v-html="$t('puzzle:kakurasu:compact.intro')"></div>
    <ul class="list-disc ml-4">
      <li v-html="$t('puzzle:kakurasu:compact.rule_row')"></li>
      <li v-html="$t('puzzle:kakurasu:compact.rule_col')"></li>
    </ul>
  </div>
</template>

