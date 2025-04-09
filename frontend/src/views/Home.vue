<script setup lang="ts">
import PuzzleMinesweeeper from "@/features/games/minesweeper/minesweeper.puzzle.vue";
import PuzzleSudoku from "@/features/games/sudoku/sudoku.puzzle.vue";
import PuzzleTents from "@/features/games/tents/tents.puzzle.vue";
import PuzzleKakurasu from "@/features/games/kakurasu/kakurasu.puzzle.vue";
import { useAppConfig } from "@/store/config";
import { usePuzzleStore } from "@/store/game";
import * as adapter from "@/store/adapters";
import { defineComponent, h } from "vue";

const settings = useAppConfig();
settings.fetchGameSettings();

// define component
const HomeGamebox = defineComponent({
  props: {
    title: { type: String, required: true },
    url: { type: String, required: true },
  },
  setup(props, { slots }) {
    return () =>
      h("div", { class: "aspect-square" }, [
        h("a", { href: props.url }, [
          h("div", { class: "select-none pointer-events-none" }, slots.default?.()),
          h("p", { class: "text-2xl mt-1 w-full text-center underline" }, props.title),
        ]),
      ]);
  },
});

// import game store
const { state: state_minesweeper } = await usePuzzleStore().usePuzzle(
  "minesweeper",
  "default",
  adapter.minesweeperAdapter,
);
const { state: state_sudoku } = await usePuzzleStore().usePuzzle("sudoku", "default", adapter.sudokuAdapter);
const { state: state_tents } = await usePuzzleStore().usePuzzle("tents", "default", adapter.tentsAdapter);
const { state: state_kakurasu } = await usePuzzleStore().usePuzzle("kakurasu", "default", adapter.kakurasuAdapter);
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

  <p>
    mitpuzzles.com is a website that lets you lorem ipsum dolor sit amet consectetur adipisicing elit. Autem est
    inventore consequatur non? Aspernatur quos sed culpa, quia animi corrupti qui in tempore delectus voluptatibus
    necessitatibus quod provident voluptates sit!
  </p>
  <div class="divider my-0"></div>
  <div class="grid grid-cols-2 md:grid-cols-3 gap-2 items-end md:mx-10 p-1">
    <HomeGamebox title="Minesweeper" url="/minesweeper">
      <PuzzleMinesweeeper :state="state_minesweeper" />
    </HomeGamebox>

    <HomeGamebox title="Sudoku" url="/sudoku">
      <PuzzleSudoku :state="state_sudoku" />
    </HomeGamebox>

    <HomeGamebox title="Tents" url="/tents">
      <PuzzleTents :state="state_tents" />
    </HomeGamebox>

    <HomeGamebox title="Kakurasu" url="/kakurasu">
      <PuzzleKakurasu :state="state_kakurasu" />
    </HomeGamebox>
  </div>
</template>
