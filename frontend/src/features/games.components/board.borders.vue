<script setup lang="ts">
import { inject, type Ref } from "vue";
import { useGridPositions, useGridLayout } from "@/features/games.components/useGridLayout.ts";
import { useBorderCalculation } from "@/features/games.components/useBorderCalculation.ts";
import type { BoardContext } from "@/features/games.components/board.ts";
import { useBorderOffsets } from "@/features/games.components/useBorderOffsets.ts";
import { useGutterBorders } from "@/features/games.components/useGutterBorders.ts";

const board = inject<BoardContext>("boardContext")!;
const offset = useBorderOffsets(board);
const layout = useGridLayout(board);
const positions = useGridPositions(board);
const borderCalc = useBorderCalculation(board);

const gutterBorders = [
  { side: "top", data: useGutterBorders("top"), count: board.gutters.top },
  { side: "bottom", data: useGutterBorders("bottom"), count: board.gutters.bottom },
  { side: "left", data: useGutterBorders("left"), count: board.gutters.left },
  { side: "right", data: useGutterBorders("right"), count: board.gutters.right },
];
</script>

<template>
  <!-- horizontal borders segments -->
  <!-- key chosen to force re-render when rows/cols change -->
  <template v-for="gutter in gutterBorders" :key="gutter.side">
    <div class="relative" v-if="(layout[`has_${gutter.side}_gutter` as keyof typeof layout] as Ref<boolean>).value">
      <!-- horizontal border segments -->
      <div v-for="(border, index) in gutter.data.borderHorizontal.value" :key="`h-${gutter.side}-${index}`">
        <div
          v-for="(_, ic) in gutter.data.colCount.value"
          :key="`h-${gutter.side}-${index}-${ic}`"
          class="absolute"
          :style="{
            left: gutter.data.startX.value + gutter.data.colOffsets.value[ic] + 'px',
            top: gutter.data.startY.value + border.top - (border.style.thickness ?? board.gap) + 'px',
            width: board.cellSize + 'px',
            height: (border.style.thickness ?? board.gap) + 'px',
            backgroundColor: 'black',
          }"
        ></div>
      </div>

      <!-- vertical border segments -->
      <div v-for="(border, index) in gutter.data.borderVertical.value" :key="`v-${gutter.side}-${index}`">
        <div
          v-for="(_, ir) in gutter.data.rowCount.value"
          class="absolute"
          :style="{
            top: gutter.data.startY.value + gutter.data.rowOffsets.value[ir] + 'px',
            left: gutter.data.startX.value + border.left - (border.style.thickness ?? board.gap) + 'px',
            width: (border.style.thickness ?? board.gap) + 'px',
            height: board.cellSize + 'px',
            backgroundColor: 'black',
          }"
        ></div>
      </div>

      <!-- Background filler -->
      <div
        v-for="(border, _) in gutter.data.borderHorizontal.value"
        class="absolute -z-9000"
        :style="{
          left: gutter.data.startX.value + 'px',
          top: gutter.data.startY.value + border.top - (border.style.thickness ?? board.gap) + 'px',
          height: (border.style.thickness ?? board.gap) + 'px',
          width: gutter.data.width.value + 'px',
          backgroundColor: 'black',
        }"
      ></div>

      <!-- Outer borders -->
      <div
        class="absolute"
        :class="borderCalc.border_class"
        :style="gutter.data.outerBorders.border1.value"
        :key="'b1-' + gutter.data.outerBorders.border1.value.left"
      ></div>
      <div
        class="absolute"
        :class="borderCalc.border_class"
        :style="gutter.data.outerBorders.border2.value"
        :key="'b2-' + gutter.data.outerBorders.border2.value.left"
      ></div>
      <div
        class="absolute"
        :class="borderCalc.border_class"
        :style="gutter.data.outerBorders.border3.value"
        :key="'b3-' + gutter.data.outerBorders.border3.value.left"
      ></div>
    </div>
  </template>

  <!-- Game Grid Borders -->
  <div class="relative">
    <!-- horizontal border segments -->
    <!-- key chosen to force re-render when rows/cols change -->
    <div v-for="(border, index) in borderCalc.game_grid_borders_row.value" :key="`h-${index}-${board.cols}`">
      <div
        v-for="(_, ic) in board.cols"
        class="absolute"
        :style="{
          left: positions.gameGridStartX.value + offset.gameInnerBorderOffsetsX.value[ic] + 'px',
          top: positions.gameGridStartY.value + border.top - (border.style.thickness ?? board.gap) + 'px',
          width: board.cellSize + 'px',
          height: (border.style.thickness ?? board.gap) + 'px',
          backgroundColor: 'black',
        }"
      ></div>
    </div>

    <!-- vertical border segments -->
    <!-- key chosen to force re-render when rows/cols change -->
    <div v-for="(border, index) in borderCalc.game_grid_borders_column.value" :key="`h-${index}-${board.rows}`">
      <div
        v-for="(_, ir) in board.rows"
        class="absolute"
        :style="{
          left: positions.gameGridStartX.value + border.left - (border.style.thickness ?? board.gap) + 'px',
          top: positions.gameGridStartY.value + offset.gameInnerBorderOffsetsY.value[ir] + 'px',
          width: (border.style.thickness ?? board.gap) + 'px',
          height: board.cellSize + 'px',
          backgroundColor: 'black',
        }"
      />
    </div>

    <!-- horizontal lines to cover the square gaps between borders -->
    <!-- IF SOMEONE DECIDES AT ONE POINT THAT THEY WANT TO HAVE THE GAPS BETWEEN THE BORDERS BE -->
    <!-- CUSTOMIZABLE OR SELECTABLE, THIS IS THE PLACE TO START LOOKING INTO THAT. THIS IS WHERE WE COVER THEM -->
    <!-- WITH A FULLY BLACK ROW BEHIND THE SEGMENTED ROWS. Easier than calculating each square position... -->
    <div
      v-for="border in borderCalc.game_grid_borders_row.value"
      class="absolute -z-9000"
      :style="{
        left: positions.gameGridStartX.value + 'px',
        top: positions.gameGridStartY.value + border.top - (border.style.thickness ?? board.gap) + 'px',
        height: (border.style.thickness ?? board.gap) + 'px',
        width: layout.gameGridWidth.value + 'px',
        backgroundColor: 'black',
      }"
    />

    <!-- Outer borders -->
    <!-- Game Grid -->
    <div class="absolute" :class="borderCalc.border_class" :style="borderCalc.border_style_top.value"></div>
    <div class="absolute" :class="borderCalc.border_class" :style="borderCalc.border_style_bottom.value"></div>
    <div class="absolute" :class="borderCalc.border_class" :style="borderCalc.border_style_right.value"></div>
    <div class="absolute" :class="borderCalc.border_class" :style="borderCalc.border_style_left.value"></div>
  </div>
</template>
