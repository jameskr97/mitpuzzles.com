<script setup lang="ts">
import { inject } from "vue";
import { useGridLayout } from "@/features/games/components/useGridLayout.ts";
import type { BoardContext } from "@/features/games/components/board.ts";

const board = inject<BoardContext>("boardContext")!;
const layout = useGridLayout(board);
</script>

<template>
  <!-- Game Grid -->
  <div :style="{ width: layout.gameGridWidth + 'px', height: layout.gameGridHeight + 'px' }">
    <div v-for="(_, ir) in board.rows" :key="ir">
      <!-- The actual cells -->
      <div
        v-for="(_, ic) in board.cols"
        :style="[layout.cellPositionGame(ir, ic)]"
        class="@container w-full h-full text-center focus:outline-none absolute"
        tabindex="-1"
      >
        <div class="text-[70cqw] w-full h-full">
          <slot name="cell" :row="ir" :col="ic" :index="ir * board.cols! + ic" />
        </div>
      </div>
    </div>
  </div>

  <!-- Gutter Top -->
  <div v-if="layout.has_top_gutter" v-for="(_, ir) in board.gutters.top" :key="ir">
    <!-- The actual cells -->
    <div
      v-for="(_, ic) in board.cols"
      :style="[layout.cellPositionGutterTop(ir, ic)]"
      class="@container w-full h-full text-center focus:outline-none absolute"
      tabindex="-1"
    >
      <div class="text-[70cqw] w-full h-full">
        <slot name="top" :row="ir" :col="ic" :index="ir * board.cols! + ic" />
      </div>
    </div>
  </div>

  <!-- Gutter Bottom -->
  <div v-if="layout.has_bottom_gutter" v-for="(_, ir) in board.gutters.bottom" :key="ir">
    <!-- The actual cells -->
    <div
      v-for="(_, ic) in board.cols"
      :style="[layout.cellPositionGutterBottom(ir, ic)]"
      class="@container w-full h-full text-center focus:outline-none absolute"
      tabindex="-1"
    >
      <div class="text-[70cqw] w-full h-full">
        <slot name="bottom" :row="ir" :col="ic" :index="ir * board.cols! + ic" />
      </div>
    </div>
  </div>

  <!-- Gutter Left -->
  <div v-if="layout.has_left_gutter" v-for="(_, ir) in board.rows" :key="ir">
    <!-- The actual cells -->
    <div
      v-for="(_, ic) in board.gutters.left"
      :style="[layout.cellPositionGutterLeft(ir, ic)]"
      class="@container w-full h-full text-center focus:outline-none absolute"
      tabindex="-1"
    >
      <div class="text-[70cqw] w-full h-full">
        <slot name="left" :row="ir" :col="ic" :index="ir * board.cols! + ic" />
      </div>
    </div>
  </div>

  <!-- Gutter Right -->
  <div v-if="layout.has_right_gutter" v-for="(_, ir) in board.rows" :key="ir">
    <!-- The actual cells -->
    <div
      v-for="(_, ic) in board.gutters.right"
      :style="[layout.cellPositionGutterRight(ir, ic)]"
      class="@container w-full h-full text-center focus:outline-none absolute"
      tabindex="-1"
    >
      <div class="text-[70cqw] w-full h-full">
        <slot name="right" :row="ir" :col="ic" :index="ir * board.cols! + ic" />
      </div>
    </div>
  </div>
</template>
