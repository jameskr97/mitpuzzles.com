<script setup lang="ts"></script>

<template>
  <div class="points-counter">
    <div class="outer-border">
      <div class="inner-border">
        <div id="pointsTally" class="points-tally number-0">
          <span id="pointsLabel">Points</span>
          <span id="pointsValue" style="font-weight: bold">0000</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.outer-border {
  width: 190px;
  height: 61px;
  background-color: rgb(189, 189, 189);
  border-top: 3px solid white;
  border-left: 3px solid white;
  border-bottom: 3px solid rgb(123, 123, 123);
  border-right: 3px solid rgb(123, 123, 123);
  position: relative; /* For positioning the inner div */
}

.inner-border {
  position: absolute;
  top: 6px;
  left: 6px;
  right: 6px;
  bottom: 6px;
  background-color: rgb(189, 189, 189);
  border-top: 3px solid rgb(123, 123, 123);
  border-left: 3px solid rgb(123, 123, 123);
  border-bottom: 3px solid white;
  border-right: 3px solid white;
  /* position: relative; */
}

#pointsCounter {
  margin-bottom: 7px;
}

.points-tally {
  display: inline-block;
  padding: 3px 3px;
  margin-top: 5px;
  color: rgb(241, 213, 1);
  background-color: black;
  /* font-family: 'Courier New', monospace; */
  font-family: "Source Code Pro", monospace;
  font-size: 1.4em;
  /* position: absolute; */
  /* top: 50%; */
  /* left: 50%; */
  /* transform: translate(-50%, -50%); */
}

@keyframes sparkAnimation {
  0% {
    opacity: 1;
    transform: translate(0, 0) scale(1);
  }
  100% {
    opacity: 0.3;
    transform: translate(X, Y) scale(0); /* Replace X, Y with target coordinates */
  }
}

.spark {
  position: absolute;
  width: 25px;
  height: 25px;
  background-color: yellow;
  border-radius: 50%;
  animation: sparkAnimation 1s ease-out forwards;
}
</style>
