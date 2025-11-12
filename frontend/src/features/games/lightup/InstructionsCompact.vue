<script setup lang="ts">
</script>

<template>
  <div>
    <div class="mb-2">{{ $t('puzzle:lightup:compact.intro') }}</div>
    <ul class="list-disc ml-4">
      <li>{{ $t('puzzle:lightup:compact.rule_illuminate') }}</li>
      <li v-html="$t('puzzle:lightup:compact.rule_no_touch')"></li>
      <li>{{ $t('puzzle:lightup:compact.rule_numbered') }}</li>
    </ul>
  </div>

</template>

