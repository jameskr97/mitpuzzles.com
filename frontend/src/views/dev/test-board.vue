<script setup lang="ts">
import BoardCells from "@/features/games/components/board.cellgrid.vue";
import BoardContainer from "@/features/games/components/board.container.vue";
import BoardBorders from "@/features/games/components/board.borders.vue";
import BoardInteraction from "@/features/games/components/board.interaction.vue";
import { computed, ref } from "vue";
import { remap } from "@/services/util.ts";

// Reactive board and gutter dimensions
const r = ref(10);
const c = ref(10);
const gutterTop = ref(0);
const gutterBottom = ref(0);
const gutterLeft = ref(0);
const gutterRight = ref(0);

const nthCol = ref(5);
const nthRow = ref(5);
const outerThickness = ref(2);
const borderConfig = computed(() => ({
  everyNthCol: { n: nthCol.value, style: { thickness: outerThickness.value } },
  everyNthRow: { n: nthRow.value, style: { thickness: outerThickness.value } },
  outer: { thickness: outerThickness.value, borderClass: "bg-black" },
}));

// Debug Panel Variables
const scale = ref(1);
const scale_remapped = computed(() => remap([0, 100], [2, 6], scale.value));
const input_history = ref<Record<string, any>>({});

// const borderConfig = {
//   everyNthCol: { n: 5, style: { thickness: 2 } },
//   everyNthRow: { n: 5, style: { thickness: 2 } },
//   outer: { thickness: 2, borderClass: "bg-black" },
// };
</script>

<template>
  <div class="grid grid-cols-[1fr_2fr] w-full mb-4 gap-2">
    <div class="flex flex-col border border-slate-300 rounded p-2 shadow">
      <p class="text-center font-bold text-3xl">Board Variables</p>
      <table class="table table-xs">
        <thead>
          <tr>
            <th>Parameter</th>
            <th>Value</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>Rows</td>
            <td><input type="number" v-model="r" min="1" class="input input-xs w-full" /></td>
          </tr>
          <tr>
            <td>Cols</td>
            <td><input type="number" v-model="c" min="1" class="input input-xs w-full" /></td>
          </tr>
          <tr>
            <td>Gutter Top</td>
            <td><input type="number" v-model="gutterTop" min="0" class="input input-xs w-full" /></td>
          </tr>
          <tr>
            <td>Gutter Bottom</td>
            <td><input type="number" v-model="gutterBottom" min="0" class="input input-xs w-full" /></td>
          </tr>
          <tr>
            <td>Gutter Left</td>
            <td><input type="number" v-model="gutterLeft" min="0" class="input input-xs w-full" /></td>
          </tr>
          <tr>
            <td>Gutter Right</td>
            <td><input type="number" v-model="gutterRight" min="0" class="input input-xs w-full" /></td>
          </tr>
          <tr>
            <td>Scale</td>
            <td class="flex flex-row gap-3">
              {{ scale }}
              <input type="range" min="0" max="100" step="1" v-model="scale" class="w-full" />
            </td>
          </tr>
          <tr>
            <td>Scale Remapped</td>
            <td>{{ Math.round(scale_remapped * 100) / 100 }}</td>
          </tr>

          <tr>
            <td>Every Nth Col</td>
            <td><input type="number" v-model="nthCol" min="0" class="input input-xs w-full" /></td>
          </tr>
          <tr>
            <td>Every Nth Row</td>
            <td><input type="number" v-model="nthRow" min="0" class="input input-xs w-full" /></td>
          </tr>
          <tr>
            <td>Outer Border Thickness</td>
            <td><input type="number" v-model="outerThickness" min="0" class="input input-xs w-full" /></td>
          </tr>
        </tbody>
      </table>
    </div>

     <div class="border max-w-fit mx-auto border-slate-300 rounded p-2 shadow mt-10">
      <BoardContainer
        :cols="c"
        :rows="r"
        :scale="scale_remapped"
        :gap="1"
        :gutter-top="gutterTop"
        :gutter-left="gutterLeft"
        :gutter-bottom="gutterBottom"
        :gutter-right="gutterRight"
        :border-config="borderConfig"
      >
        <BoardBorders />
        <BoardInteraction @input-event="(e) => (input_history[e.event_type] = e.payload)" />
        <BoardCells>
          <template #cell="{ row, col }">
            <div class="w-full h-full text-[4px] bg-slate-500">{{ row }},{{ col }}</div>
          </template>
          <template #top="{ row, col }">
            <div class="w-full h-full text-[4px] bg-blue-500">{{ row }},{{ col }}</div>
          </template>
          <template #bottom="{ row, col }">
            <div class="w-full h-full text-[4px] bg-red-500">{{ row }},{{ col }}</div>
          </template>
          <template #left="{ row, col }">
            <div class="w-full h-full text-[4px] bg-green-500">{{ row }},{{ col }}</div>
          </template>
          <template #right="{ row, col }">
            <div class="w-full h-full text-[4px] bg-yellow-500">{{ row }},{{ col }}</div>
          </template>
        </BoardCells>
      </BoardContainer>
    </div>
  </div>

  <div class="grid grid-cols-[1fr_2fr] items-start">
    <div class="flex flex-col border border-slate-300 rounded p-2 shadow max-h-fit">
      <p class="text-center font-bold text-3xl">Input History</p>
      <table class="table table-xs text-xs">
        <thead>
          <tr>
            <th>Event Type</th>
            <th>Payload</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="[event, payload] in Object.entries(input_history)" :key="event">
            <td>{{ event }}</td>
            <td>
              <pre>{{ JSON.stringify(payload, null, 2) }}</pre>
            </td>
          </tr>
        </tbody>
      </table>
      <!--      <code class="text-xs"><pre>{{ JSON.stringify(Object.entries(input_history), null, 2) }}</pre></code>-->
    </div>

  </div>
</template>
