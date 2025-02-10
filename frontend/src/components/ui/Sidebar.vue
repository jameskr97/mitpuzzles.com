<script setup lang="ts">
const games = [
  { name: "Minesweeper 💣", slug: "game-minesweeper", newBadge: true },
  // { name: "Tents ⛺", slug: "game-tents", newBadge: true },
  // { name: "Sudoku 🧩", slug: "game-sudoku", newBadge: true },
  // { name: "Pipes 🔗", slug: "game-pipes", newBadge: true },
];
</script>

<template>
  <div class="flex flex-row max-w-55 p-0">
    <div class="menu bg-base-200 text-base-content min-h-full p-0">
      <!-- Sidebar Header Image -->
      <router-link to="/">
        <img
          class="max-w-full"
          src="https://placehold.co/1000x600?text=Wow\nPlaceholder\nText"
        />
      </router-link>
      <!-- Games List -->
      <li class="text-lg mx-auto mt-2 sticky top-0">Logic Games</li>
      <div class="p-2">
        <router-link
          v-for="game in games"
          :key="game.slug"
          :to="{ name: game.slug }"
        >
          <li class="m-0">
            <a href="#">
              {{ game.name }}
              <span
                v-if="game.newBadge"
                class="inline badge badge-success badge-sm"
              >
                New!
              </span>
            </a>
          </li>
        </router-link>
      </div>

      <!-- Sidebar Footer -->
      <div
        class="flex flex-col justify-between mt-auto p-2 border border-red-600 sticky bottom-0 bg-base-200 w-full"
      >
        <p>Want to track your scores?</p>
        <p>Create an account!</p>
      </div>
    </div>
  </div>
</template>
