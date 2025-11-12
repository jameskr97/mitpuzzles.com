<template>
  <ul class="list-disc ml-4">
    <li>{{ $t('puzzle:nonograms:compact.rule_runs') }}</li>
    <li v-html="$t('puzzle:nonograms:compact.rule_mark')"></li>
    <li v-html="$t('puzzle:nonograms:compact.rule_separation')"></li>
  </ul>
</template>

