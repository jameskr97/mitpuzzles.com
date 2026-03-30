<script setup lang="ts">
import { ChevronsUpDown, LogOut, Settings } from "lucide-vue-next";

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
  DropdownMenuLabel,
} from "@/core/components/ui/dropdown-menu";
import { SidebarMenu, SidebarMenuButton, SidebarMenuItem } from "@/core/components/ui/sidebar";
import { useAuthStore } from "@/core/store/useAuthStore.ts";
import UserAvatar from "@/features/auth/components/UserAvatar.vue";
import { useRouter } from "vue-router";
import { ADMIN_TOOLS } from "@/constants.ts";

const user = useAuthStore();
const router = useRouter();
</script>

<template>
  <SidebarMenu>
    <SidebarMenuItem>
      <DropdownMenu>
        <DropdownMenuTrigger as-child>
          <SidebarMenuButton
            data-testid="sidebar-user-menu"
            size="lg"
            class="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground"
          >
            <UserAvatar class="h-8 w-8 rounded-lg" />
            <div class="grid flex-1 text-left text-sm leading-tight">
              <span class="truncate font-semibold">{{ user.user!.username }}</span>
            </div>
            <ChevronsUpDown class="ml-auto size-4" />
          </SidebarMenuButton>
        </DropdownMenuTrigger>
        <DropdownMenuContent
          class="w-[--reka-dropdown-menu-trigger-width] min-w-56 rounded-lg"
          side="top"
          align="center"
          :side-offset="4"
        >
          <DropdownMenuItem @click="router.push('/account')">
            <Settings />
            {{ $t("ui:nav.account_settings") }}
          </DropdownMenuItem>

          <!-- admin tools -->
          <template v-if="user.isAdmin">
            <DropdownMenuSeparator />
            <DropdownMenuLabel class="text-xs text-gray-400">Admin</DropdownMenuLabel>
            <router-link v-for="tool in Object.values(ADMIN_TOOLS)" :key="tool.key" :to="tool.route_path">
              <DropdownMenuItem>
                <span>{{ tool.icon }}</span>
                {{ tool.name }}
              </DropdownMenuItem>
            </router-link>
          </template>

          <DropdownMenuSeparator />
          <DropdownMenuItem data-testid="btn-logout" @click="user.logout">
            <LogOut />
            {{ $t("ui:nav.logout") }}
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </SidebarMenuItem>
  </SidebarMenu>
</template>
