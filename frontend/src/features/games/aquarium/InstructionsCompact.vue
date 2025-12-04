<template>
  <div>
    <div v-html="$t('puzzle:aquarium:compact:intro')"></div>
    <ul class="list-disc ml-4">
      <li v-html="$t('puzzle:aquarium:compact:rule_hints')"></li>
      <li v-html="$t('puzzle:aquarium:compact:rule_gravity')"></li>
    </ul>
  </div>
</template>
