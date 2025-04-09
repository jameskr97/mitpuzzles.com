<script setup lang="ts">
import { useCurrentPuzzle, useGameLayout } from "@/composables";
import { getGameScale } from "@/store/scale";
import { GameResultStatus } from "@/store/game";

const layout = useGameLayout();
const { scale, scale_remapped } = getGameScale();
const puzzle = await useCurrentPuzzle();
</script>

<template>
  <div class="flex flex-col md:flex-row h-full">
    <div class="w-full mx-auto p-2">
      <div class="h-full flex flex-col">
        <!-- GAME CONTROL BAR -->
        <div class="flex flex-col">
          <div class="flex flex-col items-center w-full md:w-3/5 2xl:w-1/3 mx-auto justify-around gap-2 px-2">
            <div class="flex flex-row w-full">
              <v-icon
                name="hi-information-circle"
                :scale="1.5"
                class="mr-2 cursor-pointer"
                @click="layout.toggle_instructions()"
              />
              <v-icon
                name="md-leaderboard"
                :scale="1.5"
                class="mr-2 cursor-pointer"
                @click="layout.toggle_leaderboard()"
              />
              <div class="tooltip tooltip-bottom w-full" data-tip="Resize Game Board">
                <input v-model="scale" type="range" min="0" max="100" class="range w-full" />
              </div>
              <div class="divider divider-horizontal mx-2"></div>
              <div class="text-2xl text-right font-mono">
                <span>{{ puzzle.timer.display_time }}</span>
              </div>
            </div>

            <!-- Buttons -->
            <div class="grid grid-cols-3 w-full gap-1">
              <button class="btn btn-error" @click="puzzle.reset" :disabled="puzzle.is_solved.value">Clear</button>
              <button class="btn btn-info" @click="puzzle.request_new">New Puzzle</button>
              <button class="btn btn-success" @click="puzzle.check_solution" :disabled="puzzle.is_solved.value">
                Submit
              </button>
            </div>
          </div>
        </div>

        <!-- Divider between control bar and game content -->
        <div class="divider divider-vertical my-2"></div>

        <div class="grid gap-2 md:gap-0 md:grid-cols-[1fr_2fr_1fr] h-full items-start">
          <!-- The GameContent itself -->
          <div
            class="z-100 order-first md:order-1 grid grid-cols-1 place-items-center mb-2 mx-2"
            :class="layout.instructions_visible.value ? '' : 'md:col-start-2'"
          >
            <div class="w-full mb-2">
              <div :class="{ hidden: puzzle.game_result_status.value !== GameResultStatus.Correct }">
                <div role="alert" class="alert alert-success flex flex-row justify-start">
                  <v-icon name="fa-check-circle" scale="1.5" />
                  <span>Your solution is correct</span>
                  <button class="btn btn-outline ml-auto" @click="puzzle.request_new">New puzzle</button>
                </div>
              </div>

              <div :class="{ hidden: puzzle.game_result_status.value !== GameResultStatus.Wrong }">
                <div role="alert" class="alert alert-error flex flex-row">
                  <v-icon name="io-close" scale="1.5" />
                  <span>Not quite!</span>
                </div>
              </div>
            </div>

            <div
              class="select-none"
              :class="puzzle.game_result_status.value === GameResultStatus.Correct ? 'pointer-events-none' : ''"
            >
              <slot name="default" :scale="scale_remapped"></slot>
            </div>
          </div>

          <!-- Game Instructions root container -->
          <div class="z-100 bg-white flex flex-col gap-2 order-1 md:order-first">
            <div
              class="border-2 border-yellow-300 shadow rounded p-2"
              :class="{
                hidden: !layout.instructions_visible.value,
              }"
            >
              <div class="flex flex-col md:w-full">
                <div class="flex flex-row align-middle justify-between">
                  <p class="text-xl text-center md:text-left">Game Instructions</p>
                  <v-icon
                    class="mt-1 cursor-pointer"
                    name="io-close"
                    @click="layout.instructions_visible.value = false"
                  />
                </div>
                <div class="divider divider-vertical p-0 m-0"></div>
                <ul class="list-inside list-decimal text-xs">
                  <slot name="instructions"></slot>
                </ul>
              </div>
            </div>
          </div>

          <!-- Leaderboard container -->
          <div
            class="z-100 bg-white order-last border-2 border-yellow-300 shadow rounded p-2 w-full"
            :class="{
              hidden: !layout.leaderboard_visible.value,
            }"
          >
            <div class="flex flex-row align-middle justify-between">
              <p class="text-xl text-center md:text-left">Leaderboard</p>
              <v-icon class="mt-1 cursor-pointer" name="io-close" @click="layout.leaderboard_visible.value = false" />
            </div>
            <div class="overflow-x-auto">
              <table class="table table-xs">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Time</th>
                    <th>Username</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <th>1</th>
                    <td>18s</td>
                    <td>User 1</td>
                  </tr>
                  <tr>
                    <th>2</th>
                    <td>30s</td>
                    <td>User 2</td>
                  </tr>
                  <tr>
                    <th>3</th>
                    <td>45s</td>
                    <td>User 3</td>
                  </tr>
                  <tr>
                    <th>4</th>
                    <td>59s</td>
                    <td>User 4</td>
                  </tr>
                  <tr>
                    <th>5</th>
                    <td>1:01</td>
                    <td>User 5</td>
                  </tr>
                  <tr>
                    <th>6</th>
                    <td>1:12</td>
                    <td>User 6</td>
                  </tr>
                  <tr>
                    <th>7</th>
                    <td>1:45</td>
                    <td>User 7</td>
                  </tr>
                  <tr>
                    <th>8</th>
                    <td>2:05</td>
                    <td>User 8</td>
                  </tr>
                  <tr>
                    <th>9</th>
                    <td>2:34</td>
                    <td>User 9</td>
                  </tr>
                  <tr>
                    <th>10</th>
                    <td>3:10</td>
                    <td>User 10</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
