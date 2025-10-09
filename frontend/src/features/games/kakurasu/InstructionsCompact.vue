<script setup lang="ts">
</script>

<template>
  <div>
    <div>Mark cells black (<span class="inline-block h-3 w-3 bg-black"></span>) so that</div>
    <ul class="list-disc ml-4">
      <li>Each <span class="font-bold">row's</span> black cells, multiplied by their column values (on top), equals the number to the right of that row.</li>
      <li>Each <span class="font-bold">column's</span> black cells, multiplied by their row values (on the left), equals the number at the bottom of that column.</li>
    </ul>
  </div>
</template>

