<script setup lang="ts">
</script>

<template>
  <div>
    <ul class="list-disc ml-4">
      <li v-html="$t('puzzle:tents:compact.rule_pairing')"></li>
      <li>{{ $t('puzzle:tents:compact.rule_no_touch') }}</li>
      <li>{{ $t('puzzle:tents:compact.rule_counts') }}</li>
    </ul>
  </div>

</template>

