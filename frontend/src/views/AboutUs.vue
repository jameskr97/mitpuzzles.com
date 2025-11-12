<script setup lang="ts">
import Container from "@/components/ui/Container.vue";
import { Separator } from "@/components/ui/separator";
</script>

<template>
  <Container class="prose prose-sm prose-tight mx-auto [&amp;_h1]:mb-1 [&amp;_h1]:mt-2 [&amp;_h2]:mt-4 [&amp;_h2]:mb-1 [&amp;_h3]:mt-2 [&amp;_h3]:mb-1 [&amp;_p]:my-1 [&amp;_ul]:my-1 [&amp;_ul]:space-y-0 [&amp;_li]:my-0">
    <img src="/assets/logo.dark.png" alt="mitpuzzles.com logo" class="p-3 mb-0 mx-auto dark:hidden" width="300" />
    <img src="/assets/logo.light.png" alt="mitpuzzles.com logo" class="p-3 mb-0 mx-auto hidden dark:block" width="300" />

    <Separator />
    <div class="text-xl m-2">
      We're researchers from MIT, Harvard, NYU, and the University of Edinburgh,
      interested in understanding how people solve complex problems.
    </div>

    <Separator />
    <div class="grid grid-cols-2 justify-items-center p-4 gap-2">
      <Container class="w-full">
        <img src="/assets/logo.mit-red.svg" />
      </Container>
      <Container class="w-full p-4">
        <img src="/assets/logo.harvard.svg" class="ml-1" />
      </Container>
      <Container class="w-full">
        <img src="/assets/logo.nyu.svg" />
      </Container>
      <Container class="w-full ">
        <img src="/assets/logo.edinburgh.svg" class="scale-125" />
      </Container>
    </div>

    <Separator />
    <p>
      This website hosts a number of classic logic puzzles, such as Minesweeper and Sudoku, as well as some lesser-known
      ones, like Light-Up and Tents — we hope you will enjoy them. The creators of this website are part of a
      multi-institutional collaboration between researchers at MIT, Harvard, NYU, and the University of Edinburgh
      interested in understanding how people solve complex problems.
    </p>
    <p>
      Our goal is to uncover how people manage their cognitive resources when facing challenging puzzles. We study
      decision-making, memory limitations, and strategic learning. The primary aim of this website is to gain insight
      into how puzzle-solving skills and strategies evolve over time with experience. Every click, move, and guess you
      make during gameplay provides invaluable data for our research, helping us to understand how people reason about
      complex problems.
    </p>

    <Separator />
    <h2>Our Team</h2>
    <ul>
      <li>James Roberts, Developer and Research Assistant, MIT</li>
      <li>Sam Cheyette, Postdoctoral Researcher, MIT</li>
      <li>Tony Chen, Graduate Student, MIT</li>
      <li>Matthias Hofer, Postdoctoral Researcher, MIT</li>
      <li>Fred Callaway, Postdoctoral Researcher, NYU &amp; Harvard</li>
      <li>Neil Bramley, Professor, University of Edinburgh</li>
      <li>Josh Tenenbaum, Professor, MIT</li>
    </ul>

    <h2>Privacy &amp; Ethics</h2>
    <p>
      We are committed to maintaining your privacy. All collected data is entirely anonymous and strictly for research
      purposes. Your gameplay data will never be shared commercially or used outside our scientific studies. You can
      review our privacy policy <a href="/privacy-policy">by clicking here</a>.
    </p>

    <h2>Be a Part of Science</h2>
    <p>
      When you play the puzzles on mitpuzzles.com, you’re not just solving challenges—you’re actively contributing to
      science. By playing the games on this website, you will be helping us advance our understanding of how people
      solve complex problems. So, thank you for your contribution to science, and we sincerely hope you have fun! If you
      encounter any errors or issues, please let us know by pressing the “Feedback” button and describing the issue in
      as much detail as you can. If you have any questions or concerns or would otherwise like to get in touch, please
      send an email to <a href="mailto:support@mitpuzzles.com">support@mitpuzzles.com</a>.
    </p>
  </Container>
</template>

<style scoped></style>
