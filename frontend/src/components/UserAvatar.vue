<script setup lang="ts">
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { computed, ref, type PropType } from "vue";
import { getGravatarUrl } from "@/utils.ts";
import { useAuthStore, type User } from "@/store/useAuthStore.ts";

const props = defineProps({
  user: {
    type: Object as PropType<User | null>,
    default: null,
  },
});
const avatar_url = computed(() => (props.user ? getGravatarUrl(props.user.email) : "https://placecats.com/300/300"));
</script>

<template>
  <Avatar>
    <AvatarImage v-if="props.user" :src="avatar_url" :alt="user!.username" />
    <AvatarImage v-else :src="avatar_url" alt="An placeholder avater of a cat, for the user who is not logged in" />
    <AvatarFallback class="rounded-lg"> CN </AvatarFallback>
  </Avatar>
</template>
