<template>
  <div class="grid grid-rows-2 p-4 h-full">
    <div class="flex flex-col mb-2 overflow-x-scroll h-full gap-2">
      <div class="grow">
        <slot name="instruction"></slot>
      </div>
    </div>
    <div class="mx-auto mt-auto">
      <slot name="board"></slot>
    </div>
  </div>
</template>

<style scoped></style>
