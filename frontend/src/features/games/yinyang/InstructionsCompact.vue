<script setup lang="ts"></script>

<template>
  <ul class="list-disc ml-4">
    <li v-html="$t('puzzle:yinyang:compact.rule_fill')"></li>
    <li>{{ $t('puzzle:yinyang:compact.rule_connected') }}</li>
    <li>{{ $t('puzzle:yinyang:compact.rule_no_2x2') }}</li>
  </ul>
</template>
