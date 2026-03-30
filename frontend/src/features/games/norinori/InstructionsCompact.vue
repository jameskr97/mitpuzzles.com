<script setup lang="ts"></script>

<template>
  <div>
    <p class="mb-1">{{ $t('puzzle:norinori:compact.intro') }}</p>
    <ul class="list-disc ml-4">
      <li v-html="$t('puzzle:norinori:compact.rule_two_per_region')"></li>
      <li v-html="$t('puzzle:norinori:compact.rule_domino')"></li>
      <li v-html="$t('puzzle:norinori:compact.rule_cross_region')"></li>
    </ul>
  </div>
</template>
