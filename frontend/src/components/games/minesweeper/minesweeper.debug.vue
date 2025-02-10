<script setup lang="ts">
import { MinesweeperGame } from './minesweeper';

defineProps<{
    game: MinesweeperGame;
}>();
</script>

<template>
    <div class="ms-2">
        <table class="table">
            <thead>
                <tr>
                    <th>Debug Option</th>
                    <th>Value</th>
                </tr>
            </thead>
            <tbody class="w-60">
                <tr>
                    <td>Board State Current</td>
                    <td>{{ game.board_state_current }}</td>
                </tr>
                <tr>
                    <td>Board State Previous</td>
                    <td>{{ game.board_state_previous }}</td>
                </tr>
                <tr>
                    <td>Danger Cell</td>
                    <td>
                        <code>
                            {{ game.danger_cell || '[ null ]'}}
                        </code>
                    </td>
                </tr>
            </tbody>
        </table>
    </div>
</template>