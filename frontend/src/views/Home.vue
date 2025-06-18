<script setup lang="tsx">
import HomePuzzlePreview from "@/components/home.puzzlepreview.vue";
import { ACTIVE_GAMES } from "@/main";
import { useVisitorStore } from "@/store/visitor.ts";
import { ref } from "vue";

const visitor = useVisitorStore();

const username_change_dialog = ref<HTMLDialogElement | null>(null)
const username_entry = ref("")
const error = ref("")
const change_username = async () => {
  const res = await visitor.changeUsername(username_entry.value);
  if (res && res.changed) {
    username_entry.value = "";
    username_change_dialog.value?.close();
  } else {
    if(res && 'error' in res)
      error.value = res.error.toString();
  }
}
</script>

<template>
  <div class="text-2xl text-center w-full">Welcome to mitpuzzles.com</div>
  <div class="divider my-0"></div>

  <div class="sm:hidden">
    <div role="alert" class="alert alert-info m-2">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 shrink-0 stroke-current" fill="none" viewBox="0 0 24 24">
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
        />
      </svg>
      <span>
        Thanks for visiting our website! If you're on a mobile-device, keep in mind that not all games will work
        properly through a touch screen.
      </span>
    </div>
    <div class="divider my-0"></div>
  </div>

  <p class="max-w-xl mx-auto text-base">
    Welcome to the first test version of this website! We've made available a limited set of games. For each game you
    play, your actions will be recorded once the game has been submitted and completed correctly. Please try out any of
    the games below - we'd love your help!
  </p>
  <p class="max-w-xl mx-auto text-base mt-2">
    Your username will be <span class="font-bold">{{ visitor.generated_username }}</span> on any leaderboards. You can
    <span class="text-blue-500 cursor-pointer" onclick="username_modal.showModal()">click here</span>
    to change your username.
  </p>
  <div class="divider my-0"></div>
  <div class="grid grid-cols-2 lg:grid-cols-4 xl:grid-cols-5 gap-2 mx-auto">
    <HomePuzzlePreview
      v-for="game in ACTIVE_GAMES"
      class="border rounded shadow border-gray-300"
      :title="game.name"
      :page="game.key"
      :key="game.key"
      :component="game.component"
      :state="game.default"
    />
  </div>

  <dialog ref="username_change_dialog" id="username_modal" class="modal">
    <div class="modal-box">
      <h3 class="text-lg font-bold">Enter new username</h3>
      <form class="flex flex-row gap-2 mt-2" @submit.prevent="change_username">
        <input v-model="username_entry" type="text" placeholder="Type here" class="input" autocomplete="off" />
        <button type="submit" class="btn" @click="change_username">Change Username</button>
      </form>
      <div v-if="error" class="text-red-500 mt-2">{{ error }}</div>
    </div>
    <form method="dialog" class="modal-backdrop">
      <button>close</button>
    </form>
  </dialog>
</template>
