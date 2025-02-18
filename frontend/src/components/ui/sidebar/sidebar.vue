<script setup lang="ts">
import SidebarUserAnon from "@/components/ui/sidebar/sidebar.user.anon.vue";
import SidebarUserAuth from "@/components/ui/sidebar/sidebar.user.auth.vue";
import { useAuthStore } from "@/store/auth";

const auth = useAuthStore();
auth.updateStore();
const games = [
  { name: "Minesweeper 💣", slug: "game-minesweeper", newBadge: true },
  { name: "Sudoku 🧩", slug: "game-sudoku", newBadge: true },
  { name: "About Us", slug: 'about-us', newBadge: true}
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
      <!-- <li class="text-lg mx-auto mt-2 sticky top-0">Logic Games</li> -->
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
        class="mt-auto border-t-2 h-19 border-red-60 sticky bottom-0 bg-base-200 w-full"
      >
        <SidebarUserAnon v-if="!auth.isAuthenticated" class="p-4" />
        <SidebarUserAuth v-else class="p-2" />
      </div>
    </div>
  </div>
</template>
